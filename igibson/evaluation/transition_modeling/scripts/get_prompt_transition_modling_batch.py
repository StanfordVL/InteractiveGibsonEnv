import fire
from multiprocessing import Process
from igibson.evaluation.transition_modeling.scripts.get_prompt_transition_modling import get_transition_modling_prompt
import  os
import json

def main(demo_dir,name_dir,rst_dir):
    os.makedirs(rst_dir,exist_ok=True)

    name_in_demo_dir=set()
    for demo in os.listdir(demo_dir):
        demo_name=demo.split(".")[0]
        name_in_demo_dir.add(demo_name)
    name_in_save_dir=set()
    for info in os.listdir(rst_dir):
        name_in_save_dir.add(info.split(".")[0])
    args_list=[]
    for demo_name in os.listdir(name_dir):
        demo_name=demo_name.split(".")[0].strip()
        if demo_name not in name_in_demo_dir:
            continue
        if demo_name in name_in_save_dir:
            continue
        abs_rst_path=os.path.join(rst_dir,demo_name+".json")
        args_list.append((demo_dir,demo_name,abs_rst_path))


    statistics=[]
    for args in args_list:
        try:
            rst=get_transition_modling_prompt(*args)
            statistics.append(rst)
        except Exception as e:
            print("Error in ",args[1])
            print(e)

        with open(os.path.join(rst_dir,"transition_modeling_prompts.json"), 'w') as f:
            json.dump(statistics,f,indent=4)

    with open(os.path.join(rst_dir,"transition_modeling_prompts.json"), 'w') as f:
        json.dump(statistics,f,indent=4)
    
    print("All Done!")


if __name__ == "__main__": 
    fire.Fire(main)
