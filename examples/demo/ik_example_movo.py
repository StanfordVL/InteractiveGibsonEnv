import yaml
from gibson2.core.physics.robot_locomotors import Turtlebot, JR2_Kinova, Fetch, Movo
from gibson2.core.simulator import Simulator
from gibson2.core.physics.scene import EmptyScene
from gibson2.core.physics.interactive_objects import InteractiveObj, BoxShape, YCBObject
from gibson2.utils.utils import parse_config
from gibson2.core.render.profiler import Profiler

import pytest
import pybullet as p
import numpy as np
from gibson2.external.pybullet_tools.utils import set_base_values, joint_from_name, set_joint_position, \
    set_joint_positions, add_data_path, connect, plan_base_motion, plan_joint_motion, enable_gravity, \
    joint_controller, dump_body, load_model, joints_from_names, user_input, disconnect, get_joint_positions, \
    get_link_pose, link_from_name, HideOutput, get_pose, wait_for_user, dump_world, plan_nonholonomic_motion, \
    set_point, create_box, stable_z, control_joints, get_max_limits, get_min_limits, get_sample_fn

import time
import numpy as np


def main():
    config = parse_config('../configs/fetch_p2p_nav.yaml')
    s = Simulator(mode='gui', timestep=1 / 240.0)
    scene = EmptyScene()
    s.import_scene(scene)
    movo = Movo(config)
    s.import_robot(movo)

    robot_id = movo.robot_ids[0]
    for i in range(p.getNumJoints(robot_id)):
        print(p.getJointInfo(robot_id, i))
        
    exit()


    all_joints = joints_from_names(robot_id,  [
        "linear_joint",
        "right_shoulder_pan_joint",
        "right_shoulder_lift_joint",
        "right_arm_half_joint",
        "right_elbow_joint",
        "right_wrist_spherical_1_joint",
        "right_wrist_spherical_2_joint",
        "right_wrist_3_joint",
        "left_shoulder_pan_joint",
        "left_shoulder_lift_joint",
        "left_arm_half_joint",
        "left_elbow_joint",
        "left_wrist_spherical_1_joint",
        "left_wrist_spherical_2_joint",
        "left_wrist_3_joint",
        ]
        )

    arm_joints = joints_from_names(robot_id,
                                            ['linear_joint'] + [item.format('right') for item in 
                                            ['{}_shoulder_pan_joint', 
                                            '{}_shoulder_lift_joint', 
                                            '{}_arm_half_joint', 
                                            '{}_elbow_joint',
                                            '{}_wrist_spherical_1_joint', 
                                            '{}_wrist_spherical_2_joint', 
                                            '{}_wrist_3_joint']])
    

    #finger_joints = joints_from_names(robot_id, ['l_gripper_finger_joint', 'r_gripper_finger_joint'])
    movo.robot_body.reset_position([0, 0, 0])
    movo.robot_body.reset_orientation([0, 0, 1, 0])
    x,y,z = movo.get_end_effector_position()
    #set_joint_positions(robot_id, finger_joints, [0.04,0.04])
    print(x,y,z)

    visual_marker = p.createVisualShape(p.GEOM_SPHERE, radius = 0.02)
    marker = p.createMultiBody(baseVisualShapeIndex = visual_marker)

    #max_limits = [0,0] + get_max_limits(robot_id, arm_joints) + [0.05,0.05]
    #min_limits = [0,0] + get_min_limits(robot_id, arm_joints) + [0,0]
    #rest_position = [0,0] + list(get_joint_positions(robot_id, arm_joints)) + [0.04,0.04]
    max_limits = get_max_limits(robot_id, all_joints)
    min_limits = get_min_limits(robot_id, all_joints)
    rest_position = list(get_joint_positions(robot_id, all_joints))
    joint_range = list(np.array(max_limits) - np.array(min_limits))
    joint_range = [item + 1 for item in joint_range]
    jd = [0.1 for item in joint_range]
    print(max_limits)
    print(min_limits)

    def accurateCalculateInverseKinematics(robotid, endEffectorId, targetPos, threshold, maxIter):
        sample_fn = get_sample_fn(robotid, arm_joints)
        set_joint_positions(robotid, arm_joints, sample_fn())
        it = 0
        while it < maxIter:
            jointPoses = p.calculateInverseKinematics(robotid, endEffectorId, targetPos,
                                                      lowerLimits = min_limits,
                                                      upperLimits = max_limits,
                                                      jointRanges = joint_range,
                                                      restPoses = rest_position,
                                                      jointDamping = jd)
            set_joint_positions(robotid, arm_joints, jointPoses[:8])
            ls = p.getLinkState(robotid, endEffectorId)
            newPos = ls[4]

            dist = np.linalg.norm(np.array(targetPos) - np.array(newPos))
            if dist < threshold:
                break

            it += 1

        print ("Num iter: " + str(it) + ", threshold: " + str(dist))
        return jointPoses

    while True:
        with Profiler("Simulation step"):
            movo.robot_body.reset_position([0, 0, 0])
            movo.robot_body.reset_orientation([0, 0, 1, 0])
            threshold = 0.01
            maxIter = 100
            joint_pos = accurateCalculateInverseKinematics(robot_id, movo.parts['right_gripper_link'].body_part_index, [x, y, z],
                                                           threshold, maxIter)[:8]

            #set_joint_positions(robot_id, finger_joints, [0.04, 0.04])
            s.step()
            keys = p.getKeyboardEvents()
            for k, v in keys.items():
                if (k == p.B3G_RIGHT_ARROW and (v & p.KEY_IS_DOWN)):
                    x += 0.01
                if (k == p.B3G_LEFT_ARROW and (v & p.KEY_IS_DOWN)):
                    x -= 0.01
                if (k == p.B3G_UP_ARROW and (v & p.KEY_IS_DOWN)):
                    y += 0.01
                if (k == p.B3G_DOWN_ARROW and (v & p.KEY_IS_DOWN)):
                    y -= 0.01
                if (k == ord('z') and (v & p.KEY_IS_DOWN)):
                    z += 0.01
                if (k == ord('x') and (v & p.KEY_IS_DOWN)):
                    z -= 0.01
            p.resetBasePositionAndOrientation(marker, [x,y,z], [0,0,0,1])

    s.disconnect()


if __name__ == '__main__':
    main()

