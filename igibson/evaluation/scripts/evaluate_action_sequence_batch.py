import fire
from multiprocessing import Process
from igibson.evaluation.scripts.evaluate_action_sequence_result import evaluate_action_seqeunce
import  os
import json
from igibson.evaluation.action_sequence.action_sequence_evaluator import ActionSequenceEvaluator


def evaluate_action_sequence_parsed(demo_dir,actions,demo_name,rst_path):
    os.makedirs(os.path.dirname(rst_path),exist_ok=True)
    ase=ActionSequenceEvaluator(demo_dir=demo_dir,demo_name=demo_name)
    rst=ase.evaluate_action_sequence(actions)
    with open(rst_path, 'w') as t_f:
        json.dump(rst,t_f,indent=4)
    return rst

def evaluate_action_sequence_raw(demo_dir,actions_raw,demo_name,rst_path):
    os.makedirs(os.path.dirname(rst_path),exist_ok=True)
    ase=ActionSequenceEvaluator(demo_dir=demo_dir,demo_name=demo_name)
    action_parsed=ase.parse_response(actions_raw)
    rst=ase.evaluate_action_sequence(action_parsed)
    with open(rst_path, 'w') as t_f:
        json.dump(rst,t_f,indent=4)
    return rst

def evaluate_action_sequence_batch(demo_dir, rst_dir,llm_output_path=None,llm_output_dir=None):
    assert llm_output_path is not None or llm_output_dir is not None
    args_list=[]
    if llm_output_dir is not None:
        for action_path in os.listdir(llm_output_dir):
            abs_action_path=os.path.join(llm_output_dir,action_path)
            demo_name=action_path.replace(".json","")
            actions=json.load(open(abs_action_path,'r'))
            rst_path=os.path.join(rst_dir,demo_name+".json")
            if action_path.endswith(".json"):
                args_list.append((demo_dir,actions,demo_name,rst_path))
    else:
        with open(llm_output_path, 'r') as f:
            responses = json.load(f)
        for response in responses:
            demo_name=response['identifier']
            llm_response=response['llm_output']
            args_list.append((demo_dir,llm_response,demo_name,os.path.join(rst_dir,demo_name+".json")))


    final_rst=[]

    for args in args_list:
        try:
            if llm_output_dir is not None:
                rst=evaluate_action_sequence_parsed(*args)
            else:
                rst=evaluate_action_sequence_raw(*args)

            final_rst.append(
                {
                    "identifier":args[2],
                    "llm_rst":rst
                }
            )
        except Exception as e:
            print(f"Error in {args[2]}")
            print(e)
            final_rst.append(
                {
                    "identifier":args[2],
                    "llm_rst":None
                }
            )
    

    with open(os.path.join(rst_dir,'final_rst.json'), 'w') as f:
        f.write(json.dumps(final_rst,indent=4))

    return final_rst

if __name__ == "__main__":
    fire.Fire(evaluate_action_sequence_batch)