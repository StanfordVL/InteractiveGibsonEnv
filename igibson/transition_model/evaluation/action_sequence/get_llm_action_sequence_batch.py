import fire
from multiprocessing import Process
from igibson.transition_model.evaluation.action_sequence.get_llm_action_sequence import get_llm_action_seqeunce
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

    # procs = []
    # for args in args_list:
    #     proc = Process(target=evaluate_action_seqeunce, args=args)
    #     procs.append(proc)
    #     proc.start()

    # for proc in procs:
    #     proc.join()

    statistics=[]
    for args in args_list:
        info={
            "name":args[0].split("/")[-1],
            }
        try:
            rst=get_llm_action_seqeunce(*args)
            info.update(rst)
        except Exception as e:
            print("Error in ",args[0])
            print(e)
            info.update({"error":str(e)})

        statistics.append(info)
        with open(os.path.join(rst_dir,"statistics.json"), 'w') as f:
            json.dump(statistics,f,indent=4)

    with open(os.path.join(rst_dir,"statistics.json"), 'w') as f:
        json.dump(statistics,f,indent=4)
    
    print("All Done!")


if __name__ == "__main__":  # confirms that the code is under main function
    fire.Fire(main)

# python D:\GitHub\behavior-vllm-eval\igibson\transition_model_v3\evaluation\action_sequence\get_llm_action_sequence_batch.py "D:\GitHub\behavior-vllm-eval\igibson\data\virtual_reality" "D:\GitHub\behavior-vllm-eval\igibson\transition_model_v3\data\annotations" "D:\GitHub\behavior-vllm-eval\igibson\transition_model_v3\data\gpt4_annotations"