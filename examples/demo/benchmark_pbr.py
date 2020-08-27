from gibson2.core.physics.robot_locomotors import Turtlebot
from gibson2.core.simulator import Simulator
from gibson2.core.physics.scene import BuildingScene
from gibson2.core.physics.interactive_objects import YCBObject
from gibson2.utils.utils import parse_config
import pybullet as p
import numpy as np
from gibson2.core.render.profiler import Profiler
import time
from gibson2.core.render.mesh_renderer.mesh_renderer_cpu import MeshRenderer
import sys
import os
import cv2
import pickle as pkl


def benchmark(render_to_tensor=False, resolution=512, obj_num = 100, optimize = True):
    
    n_frame = 200
    
    if optimize:
        renderer = MeshRenderer(width=512, height=512, msaa=True, vertical_fov=90, optimize=True, device_idx=1)
    else:
        renderer = MeshRenderer(width=512, height=512, msaa=True, vertical_fov=90, enable_shadow=False)

    renderer.load_object('plane/plane_z_up_0.obj', scale=[3,3,3])
    renderer.add_instance(0)
    renderer.set_pose([0,0,-1.5,1, 0, 0.0, 0.0], -1)

    
    model_path = sys.argv[1]

    px = 1
    py = 1
    pz = 1

    camera_pose = np.array([px, py, pz])
    view_direction = np.array([-1, -1, -1])
    renderer.set_camera(camera_pose, camera_pose + view_direction, [0, 0, 1])
    theta = 0
    r = 6
    scale = 1    
    i = 1

    obj_count_x = int(np.sqrt(obj_num))


    for fn in os.listdir(model_path):
        if fn.endswith('obj') and 'processed' in fn:
            renderer.load_object(os.path.join(model_path, fn), scale=[scale, scale, scale])
            for obj_i in range(obj_count_x):
                for obj_j in range(obj_count_x):        
                    renderer.add_instance(i)
                    renderer.set_pose([obj_i-obj_count_x/2., obj_j-obj_count_x/2.,0,0.7071067690849304, 0.7071067690849304, 0.0, 0.0], -1)
                    renderer.instances[-1].use_pbr = True
                    renderer.instances[-1].use_pbr_mapping = True
                    renderer.instances[-1].metalness = 1
                    renderer.instances[-1].roughness = 0.1
            i += 1
            

    print(renderer.visual_objects, renderer.instances)
    print(renderer.materials_mapping, renderer.mesh_materials)
    #print(renderer.texture_files)

    if optimize:
        renderer.optimize_vertex_and_texture()

    start = time.time()
    for i in range(n_frame):
        px = r*np.sin(theta)
        py = r*np.cos(theta)
        theta += 0.01
        camera_pose = np.array([px, py, pz])
        renderer.set_camera(camera_pose, [0,0,0], [0, 0, 1])

        frame = renderer.render(modes=('rgb'))
        #print(frame)
        # cv2.imshow('test', cv2.cvtColor(np.concatenate(frame, axis=1), cv2.COLOR_RGB2BGR))
        # cv2.waitKey(1)
    elapsed = time.time()-start
    print('{} fps'.format(n_frame/elapsed))
    return obj_num, n_frame/elapsed
def main():
    #benchmark(render_to_tensor=True, resolution=512)
    results = []
    
    for obj_num in [item **2 for item in [1,2,3,4,5,6,7,8,9,10,11,12]]:
        res = benchmark(render_to_tensor=False, resolution=512, obj_num=obj_num, optimize = False)
        results.append(res)
        pkl.dump(results, open('pbr_no_shadow.pkl', 'wb'))


if __name__ == '__main__':
    main()