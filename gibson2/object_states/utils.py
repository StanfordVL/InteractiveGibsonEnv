import numpy as np
import pybullet as p
import cv2
from gibson2.external.pybullet_tools.utils import get_link_pose, matrix_from_quat, get_aabb_center, get_aabb_extent, stable_z_on_aabb, get_aabb
from gibson2.object_states import AABB
from gibson2.object_states.object_state_base import CachingEnabledObjectState
import gibson2
from IPython import embed
from gibson2.utils import sampling_utils
from scipy.spatial.transform import Rotation as R


def get_center_extent(obj_states):
    assert AABB in obj_states
    aabb = obj_states[AABB].get_value()
    center, extent = get_aabb_center(aabb), get_aabb_extent(aabb)
    return center, extent


def clear_cached_states(obj):
    for _, obj_state in obj.states.items():
        if isinstance(obj_state, CachingEnabledObjectState):
            obj_state.clear_cached_value()


def sample_kinematics(predicate, objA, objB, binary_state, use_ray_casting_method=False):
    if not binary_state:
        raise NotImplementedError()

    sample_on_floor = predicate == 'onFloor'

    if not use_ray_casting_method and not sample_on_floor and predicate not in objB.supporting_surfaces:
        return False

    max_trials = 100
    z_offset = 0.05

    old_pos = objA.get_position()

    objA.force_wakeup()
    if not sample_on_floor:
        objB.force_wakeup()

    state_id = p.saveState()
    for i in range(max_trials):
        pos = None
        if objA.orientations is not None:
            orientation = objA.sample_orientation()
        else:
            orientation = [0, 0, 0, 1]

        # Orientation needs to be set for stable_z_on_aabb to work correctly
        objA.set_orientation(orientation)

        if sample_on_floor:
            _, pos = objB.scene.get_random_point_by_room_instance(
                objB.room_instance)
        else:
            if use_ray_casting_method:
                if predicate == 'onTop':
                    _RAY_CASTING_PARALLEL_RAY_NORMAL_ANGLE_TOLERANCE = 0.52
                    _RAY_CASTING_MAX_ANGLE_WITH_Z_AXIS = 0.17
                    _RAY_CASTING_BIMODAL_STDEV_FRACTION = 0.01
                    _RAY_CASTING_BIMODAL_MEAN_FRACTION = 1.0
                    _RAY_CASTING_MAX_SAMPLING_ATTEMPTS = 50
                    _RAY_CASTING_AABB_OFFSET = 0.1
                elif predicate == 'inside':
                    _RAY_CASTING_PARALLEL_RAY_NORMAL_ANGLE_TOLERANCE = 0.52
                    _RAY_CASTING_MAX_ANGLE_WITH_Z_AXIS = 0.17
                    _RAY_CASTING_BIMODAL_STDEV_FRACTION = 0.4
                    _RAY_CASTING_BIMODAL_MEAN_FRACTION = 0.5
                    _RAY_CASTING_MAX_SAMPLING_ATTEMPTS = 100
                    _RAY_CASTING_AABB_OFFSET = -0.01
                else:
                    assert False, \
                        'predicate is not onTop or inside: {}'.format(
                            predicate)

                aabb = get_aabb(objA.get_body_id())
                aabb_center, aabb_extent = \
                    get_aabb_center(aabb), get_aabb_extent(aabb)

                # TODO: Get this to work with non-URDFObject objects.
                sampling_results = sampling_utils.sample_cuboid_on_object(
                    objB,
                    num_samples=1,
                    max_sampling_attempts=_RAY_CASTING_MAX_SAMPLING_ATTEMPTS,
                    cuboid_dimensions=aabb_extent,
                    bimodal_mean_fraction=_RAY_CASTING_BIMODAL_MEAN_FRACTION,
                    bimodal_stdev_fraction=_RAY_CASTING_BIMODAL_STDEV_FRACTION,
                    axis_probabilities=[0, 0, 1],
                    aabb_offset=_RAY_CASTING_AABB_OFFSET,
                    max_angle_with_z_axis=_RAY_CASTING_MAX_ANGLE_WITH_Z_AXIS,
                    parallel_ray_normal_angle_tolerance=_RAY_CASTING_PARALLEL_RAY_NORMAL_ANGLE_TOLERANCE,
                    refuse_downwards=True)

                sampled_vector = sampling_results[0][0]
                sampled_quaternion = sampling_results[0][2]

                sampling_success = sampled_vector is not None
                if sampling_success:
                    # Find the delta from the object's CoM to its AABB centroid
                    diff = old_pos - aabb_center

                    sample_rotation = R.from_quat(sampled_quaternion)
                    original_rotation = R.from_quat(orientation)
                    combined_rotation = sample_rotation * original_rotation

                    # Rotate it using the quaternion
                    rotated_diff = sample_rotation.apply(diff)

                    pos = sampled_vector + rotated_diff
                    orientation = combined_rotation.as_quat()
            else:
                random_idx = np.random.randint(
                    len(objB.supporting_surfaces[predicate].keys()))
                body_id, link_id = list(objB.supporting_surfaces[predicate].keys())[
                    random_idx]
                random_height_idx = np.random.randint(
                    len(objB.supporting_surfaces[predicate][(body_id, link_id)]))
                height, height_map = objB.supporting_surfaces[predicate][(
                    body_id, link_id)][random_height_idx]
                obj_half_size = np.max(objA.bounding_box) / 2 * 100
                obj_half_size_scaled = np.array(
                    [obj_half_size / objB.scale[1], obj_half_size / objB.scale[0]])
                obj_half_size_scaled = np.ceil(
                    obj_half_size_scaled).astype(np.int)
                height_map_eroded = cv2.erode(
                    height_map, np.ones(obj_half_size_scaled, np.uint8))

                valid_pos = np.array(height_map_eroded.nonzero())
                if valid_pos.shape[1] != 0:
                    random_pos_idx = np.random.randint(valid_pos.shape[1])
                    random_pos = valid_pos[:, random_pos_idx]
                    y_map, x_map = random_pos
                    y = y_map / 100.0 - 2
                    x = x_map / 100.0 - 2
                    z = height

                    pos = np.array([x, y, z])
                    pos *= objB.scale

                    # the supporting surface is defined w.r.t to the link frame, not
                    # the inertial frame
                    if link_id == -1:
                        link_pos, link_orn = p.getBasePositionAndOrientation(
                            body_id)
                        dynamics_info = p.getDynamicsInfo(body_id, -1)
                        inertial_pos = dynamics_info[3]
                        inertial_orn = dynamics_info[4]
                        inv_inertial_pos, inv_inertial_orn =\
                            p.invertTransform(inertial_pos, inertial_orn)
                        link_pos, link_orn = p.multiplyTransforms(
                            link_pos, link_orn, inv_inertial_pos, inv_inertial_orn)
                    else:
                        link_pos, link_orn = get_link_pose(body_id, link_id)
                    pos = matrix_from_quat(link_orn).dot(
                        pos) + np.array(link_pos)
                    z = stable_z_on_aabb(
                        objA.get_body_id(), ([0, 0, pos[2]], [0, 0, pos[2]]))
                    pos[2] = z

        if pos is None:
            success = False
        else:
            pos[2] += z_offset
            objA.set_position_orientation(pos, orientation)
            p.stepSimulation()
            success = len(p.getContactPoints(objA.get_body_id())) == 0

        if gibson2.debug_sampling:
            print('sample_kinematics', success)
            embed()

        if success:
            break
        else:
            p.restoreState(state_id)

    p.removeState(state_id)

    if success:
        objA.set_position_orientation(pos, orientation)
        # Let it fall for 0.2 second
        physics_timestep = p.getPhysicsEngineParameters()['fixedTimeStep']
        for _ in range(int(0.2 / physics_timestep)):
            p.stepSimulation()
            if len(p.getContactPoints(bodyA=objA.get_body_id())) > 0:
                break

    return success
