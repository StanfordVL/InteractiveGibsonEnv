from igibson.transition_model.eval_env import EvalActions
from igibson.transition_model.eval_env import EvalEnv
import platform
import io
from contextlib import redirect_stdout
import json
import fire

def evaluate_action_seqeunce(demo_path,action_path,rst_path,headless=True):
    env=EvalEnv(demo_path=demo_path,mode="headless" if headless else "gui_non_interactive",
        use_pb_gui=(not headless and platform.system() != "Darwin"),)
    
    with open(action_path, 'r') as f:
        actions=json.load(f)

    f=io.StringIO()
    rst={
        "all_action_execution_true":True,
        "unknown_execution_error":False,
        "all_condition_satisfied":False,
    }
    with redirect_stdout(f):
        print("Addressable Objects:")
        for obj in env.addressable_objects:
            print(obj.name)
        print("-----------------------------------------------")
        print("Initial Conditions: ")
        for condition in env.task.initial_conditions:
            print(condition.terms)
        print("-----------------------------------------------")
        print("Goal Conditions: ")
        for condition in env.task.goal_conditions:
            print(condition.terms)
        print("------------Action Execution Begins-------------")
        for action in actions:
            try:
                action_name=action["action"]
                obj=action["object"]
                print("Action: ",action_name,obj)
                _,_,_,_,flag=env.apply_action(action_name,obj)
                if not flag:
                    rst["all_action_execution_true"]=False
                print("Post Effects: ",flag,env.task.check_success())

            except Exception as e:
                rst["unknown_execution_error"]=True
                print("Execution Error:",e)
            print("************************************************")

        print("------------Action Execution Ends-------------")
        if not env.task.check_success()[0]:
            print("Final teleport")
            env.final_step()
            print("Post Effects: ",env.task.check_success())
        rst["all_condition_satisfied"]=env.task.check_success()[0]
        print(rst)
        
    with open(rst_path, 'w') as t_f:
        t_f.write(f.getvalue())

    return rst

import os
def main(demo_name,action_dir="./igibson/transition_model_v3/data/human_annotations",demo_dir="./igibson/data/virtual_reality",rst_path="test.log"):
    demo_path=os.path.join(demo_dir,demo_name+".hdf5")
    action_path=os.path.join(action_dir,demo_name+".json")
    evaluate_action_seqeunce(demo_path,action_path,rst_path)
if __name__ == "__main__":
    fire.Fire(main)
"""
python D:\GitHub_jameskrw\iGibson\igibson\transition_model_v3\scripts\evaluate_action_sequence.py bottling_fruit_0_Wainscott_0_int_0_2021-05-24_19-46
"""

