import fire
from multiprocessing import Process
from igibson.transition_model.scripts.goal_condition_result_analysis import evaluate_goal_condition_seqeunce
import  os
import json

def main(rst_dir,save_dir):
    os.makedirs(save_dir,exist_ok=True)
    args_list=[]
    for rst_path in os.listdir(rst_dir):
        if rst_path.endswith(".log"):
            abs_rst_path=os.path.join(rst_dir,rst_path)
            abs_save_path=os.path.join(save_dir,rst_path)
            abs_save_path=abs_save_path.replace(".log",".json")
            args_list.append((abs_rst_path,abs_save_path))

    statistics=[]
    summary={"total_run":0}
    for args in args_list:
        info={
            "name":args[0].split("/")[-1],
            }
        try:
            rst=evaluate_goal_condition_seqeunce(*args)
            info.update(rst)
            for k,v in rst.items():
                if k in summary:
                    summary[k]+=int(v)
                else:
                    summary[k]=int(v)
            summary["total_run"]+=1
        except Exception as e:
            print("Error in ",args[0])
            print(e)
            info.update({"error":str(e)})

        statistics.append(info)
        with open(os.path.join(save_dir,"statistics.json"), 'w') as f:
            json.dump(statistics,f,indent=4)
        with open(os.path.join(save_dir,"summary.json"), 'w') as f:
            json.dump(summary,f,indent=4)
    statistics.append(summary)
    with open(os.path.join(save_dir,"statistics.json"), 'w') as f:
        json.dump(statistics,f,indent=4)
    
    print("All Done!")


if __name__ == "__main__":  # confirms that the code is under main function
    fire.Fire(main)

