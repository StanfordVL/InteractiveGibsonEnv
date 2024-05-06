from igibson.transition_model_graph.eval_evolving_graph_env import EvalGraphEnv
import platform
import io
from contextlib import redirect_stdout
import json
import fire
import traceback

def evaluate_action_seqeunce(demo_path,action_path,rst_path,headless=True):
    env=EvalGraphEnv(demo_path=demo_path,mode="headless" if headless else "gui_non_interactive",
        use_pb_gui=(not headless and platform.system() != "Darwin"),)
    
    with open(action_path, 'r') as f:
        actions=json.load(f)

    f=io.StringIO()
    rst={
        "all_action_execution_true":True,
        "unknown_execution_error":False,
        "all_condition_satisfied":False,
        "success_steps":0,
        "total_steps":len(actions),
        "missing_steps":0,
        "additional_steps":0,
        "affordance_errors":0,
        "syntax_errors":0,
        "wrong_temporal_order":0,
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
                if flag:
                    rst["success_steps"]+=1

            except Exception as e:
                rst["unknown_execution_error"]=True
                msg=traceback.format_exc()
                print("Execution Error:",msg)
            print("************************************************")
        print("------------Action Execution Ends-------------")
        rst["all_condition_satisfied"]=env.task.check_success()[0]
        rst["success_rate"]=rst["success_steps"]/rst["total_steps"] if rst["total_steps"]>0 else 0
        rst_str=f.getvalue()
        action_str_list=rst_str.split("Action: ")
        if len(action_str_list)>1:
            action_str_list=action_str_list[1:]
        for action_rst in action_str_list:
            if "Execution Error:" in action_rst:
                rst["syntax_errors"]+=1
                continue
            if "ErrorType.ADDITIONAL_STEP" in action_rst:
                count=action_rst.count("ErrorType.ADDITIONAL_STEP")
                if not (count==1 and "CLEAN" in action_rst):
                    rst["additional_steps"]+=1
                    continue
            if "ErrorType.AFFORDANCE_ERROR" in action_rst:
                rst["affordance_errors"]+=1
                continue
            if "ErrorType.WRONG_TEMPORAL_ORDER" in action_rst:
                rst["wrong_temporal_order"]+=1
                continue
            if "ErrorType.MISSING_STEP" in action_rst:
                rst["missing_steps"]+=1
                continue
        print(rst)

            
    with open(rst_path, 'w') as t_f:
        t_f.write(f.getvalue())

    return rst

import os
def main(demo_name,action_dir="./igibson/transition_model/data/human_annotations",demo_dir="./igibson/data/virtual_reality",rst_path="test.log"):
    demo_path=os.path.join(demo_dir,demo_name+".hdf5")
    action_path=os.path.join(action_dir,demo_name+".json")
    evaluate_action_seqeunce(demo_path,action_path,rst_path)
if __name__ == "__main__":
    fire.Fire(main)

