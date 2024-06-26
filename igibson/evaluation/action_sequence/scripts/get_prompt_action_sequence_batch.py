import fire
from multiprocessing import Process
from igibson.evaluation.action_sequence.scripts.get_prompt_action_sequence import get_llm_prompt
import  os
import json

def main(demo_dir,action_dir,rst_dir):
    os.makedirs(rst_dir,exist_ok=True)
    args_list=[]
    for action_path in os.listdir(action_dir):
        if action_path.endswith(".json"):
            abs_action_path=os.path.join(action_dir,action_path)
            abs_demo_path=os.path.join(demo_dir,action_path.replace(".json",".hdf5"))
            abs_rst_path=os.path.join(rst_dir,action_path)
            args_list.append((abs_demo_path,abs_rst_path))

    statistics=[]
    for args in args_list:
        try:
            rst=get_llm_prompt(*args)
            statistics.append(rst)
        except Exception as e:
            print("Error in ",args[0])
            print(e)

        with open(os.path.join(rst_dir,"action_sequence_prompts.json"), 'w') as f:
            json.dump(statistics,f,indent=4)

    with open(os.path.join(rst_dir,"action_sequence_prompts.json"), 'w') as f:
        json.dump(statistics,f,indent=4)
    
    print("All Done!")


if __name__ == "__main__": 
    fire.Fire(main)
