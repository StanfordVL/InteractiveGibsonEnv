import fire
from multiprocessing import Process
from igibson.evaluation.scripts.evaluate_action_sequence_result import evaluate_action_seqeunce
import  os
import json

def main(demo_dir,action_dir,rst_dir,headless=True):
    os.makedirs(rst_dir,exist_ok=True)
    args_list=[]
    for action_path in os.listdir(action_dir):
        if action_path.endswith(".json"):
            abs_action_path=os.path.join(action_dir,action_path)
            abs_demo_path=os.path.join(demo_dir,action_path.replace(".json",".hdf5"))
            abs_rst_path=os.path.join(rst_dir,action_path.replace(".json",".log"))
            args_list.append((abs_demo_path,abs_action_path,abs_rst_path,headless))

    # procs = []
    # for args in args_list:
    #     proc = Process(target=evaluate_action_seqeunce, args=args)
    #     procs.append(proc)
    #     proc.start()

    # for proc in procs:
    #     proc.join()

    statistics=[]
    summary={"total_run":0}
    for args in args_list:
        info={
            "name":args[1].split("/")[-1],
            }
        try:
            rst=evaluate_action_seqeunce(*args)
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
        with open(os.path.join(rst_dir,"statistics.json"), 'w') as f:
            json.dump(statistics,f,indent=4)
    statistics.append(summary)

    # caculate the statistics
    # read the last line of the log file
    # statistics=[]
    # for args in args_list:
    #     with open(args[2], 'r') as f:
    #         lines=f.readlines()
    #         last_line=lines[-1]
    #         info.update(eval(last_line))
    #     statistics.append(info)
    
    # write the statistics to a file
    with open(os.path.join(rst_dir,"statistics.json"), 'w') as f:
        json.dump(statistics,f,indent=4)
    
    print("All Done!")


if __name__ == "__main__":  
    fire.Fire(main)
