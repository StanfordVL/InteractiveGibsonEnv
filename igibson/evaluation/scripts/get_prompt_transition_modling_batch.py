import fire
from multiprocessing import Process
from igibson.evaluation.scripts.get_prompt_transition_modling import get_transition_modling_prompt
import  os
import json

def main(demo_dir,action_dir,rst_dir):
    os.makedirs(rst_dir,exist_ok=True)
    args_list=[]
    for action_path in os.listdir(action_dir):
        if action_path.endswith(".json"):
            abs_demo_name=os.path.join(action_path.replace(".json",""))
            abs_rst_path=os.path.join(rst_dir,action_path)
            args_list.append((demo_dir,abs_demo_name,abs_rst_path))

    statistics=[]
    for args in args_list:
        try:
            rst=get_transition_modling_prompt(*args)
            statistics.append(rst)
        except Exception as e:
            print("Error in ",args[1])
            print(e)

        with open(os.path.join(rst_dir,"transition_modeling_prompt.json"), 'w') as f:
            json.dump(statistics,f,indent=4)

    with open(os.path.join(rst_dir,"transition_modeling_prompt.json"), 'w') as f:
        json.dump(statistics,f,indent=4)
    
    print("All Done!")


if __name__ == "__main__": 
    fire.Fire(main)
