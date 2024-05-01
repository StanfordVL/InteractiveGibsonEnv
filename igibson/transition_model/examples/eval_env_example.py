from igibson.eval_gibson.eval_env import EvalEnv
import platform
import igibson.object_states as object_states

def main():
    demo_path=rb"D:\GitHub\behavior-vllm-eval\igibson\data\virtual_reality\bottling_fruit_0_Wainscott_0_int_0_2021-05-24_19-46-46.hdf5"
    headless = False
    env=EvalEnv(demo_path=demo_path,mode="headless" if headless else "gui_non_interactive",
            use_pb_gui=(not headless and platform.system() != "Darwin"),)
    

    for obj in env.addressable_objects:
        print(obj.name)

    for goal in env.task.natural_language_goal_conditions:
        print(goal)

    actions=[
            {'action': 'OPEN', 'object': 'fridge_97'},
            {'action': 'RIGHT_GRASP', 'object': 'strawberry_0'},
            {'action': 'LEFT_GRASP', 'object': 'peach_0'},
            {'action': 'LEFT_RELEASE', 'object': 'peach_0'},
            {'action': 'RIGHT_RELEASE', 'object': 'strawberry_0'},
            {'action': 'RIGHT_GRASP', 'object': 'carving_knife_0'},
            {'action': 'SLICE', 'object': 'strawberry_0'},
            {'action': 'SLICE', 'object': 'peach_0'},
            {'action': 'RIGHT_RELEASE', 'object': 'carving_knife_0'},
            {'action': 'OPEN', 'object': 'jar_1'},
            {'action': 'LEFT_GRASP', 'object': 'strawberry_0_part_0'},
            {'action': 'LEFT_PLACE_INSIDE', 'object': 'jar_1'},
            {'action': 'LEFT_GRASP', 'object': 'strawberry_0_part_1'},
            {'action': 'LEFT_PLACE_INSIDE', 'object': 'jar_1'},
            {'action': 'CLOSE', 'object': 'jar_1'},
            {'action': 'OPEN', 'object': 'jar_0'},
            {'action': 'LEFT_GRASP', 'object': 'peach_0_part_0'},
            {'action': 'LEFT_PLACE_INSIDE', 'object': 'jar_0'},
            {'action': 'LEFT_GRASP', 'object': 'peach_0_part_1'},
            {'action': 'LEFT_PLACE_INSIDE', 'object': 'jar_0'},
            {'action': 'CLOSE', 'object': 'jar_0'},]
    
    for action in actions:
        action_execuble=(action['action'], action['object'])
        env.step(action_execuble)

    print(env.task.check_success())


if __name__ == "__main__":
    main()
    