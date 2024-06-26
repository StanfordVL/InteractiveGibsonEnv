import fire
from multiprocessing import Process
import  os
import json
from igibson.evaluation.action_sequence.action_sequence_evaluator import ActionSequenceEvaluator
from collections import defaultdict

def evaluate_action_sequence_parsed(demo_dir,actions,demo_name,rst_path):
    os.makedirs(os.path.dirname(rst_path),exist_ok=True)
    ase=ActionSequenceEvaluator(demo_dir=demo_dir,demo_name=demo_name)
    rst=ase.evaluate_parsed(actions)
    with open(rst_path, 'w') as t_f:
        json.dump(rst,t_f,indent=4)
    return rst

def evaluate_action_sequence_raw(demo_dir,actions_raw,demo_name,rst_path):
    os.makedirs(os.path.dirname(rst_path),exist_ok=True)
    ase=ActionSequenceEvaluator(demo_dir=demo_dir,demo_name=demo_name)
    rst=ase.evaluate_all(actions_raw)
    print(rst_path)
    with open(rst_path, 'w') as t_f:
        json.dump(rst,t_f,indent=4)
    return rst

def evaluate_llm_response_batch(demo_dir,llm_response_path,rst_dir,file_name='llm_result.json'):
    os.makedirs(rst_dir,exist_ok=True)
    llm_response=json.load(open(llm_response_path))
    output=[]
    available_demo_names=[]
    for name in os.listdir(demo_dir):
        if name.endswith('.hdf5'):
            demo_name=name.split('.')[0]
            available_demo_names.append(demo_name)
    available_demo_names=set(available_demo_names)
    evaluated_demo_names=set()
    for file in os.listdir(rst_dir):
        if file.endswith('.json'):
            demo_name=file.split('.')[0]
            if demo_name in available_demo_names:
                with open(os.path.join(rst_dir,file)) as f:
                    rst=json.load(f)
                    output.append({
                        "identifier":demo_name,
                        "llm_rst":rst
                    })
                evaluated_demo_names.add(demo_name)
    for response in llm_response:
        if response['identifier'] in evaluated_demo_names:
            print('skip',response['identifier'])
            continue
        identifier=response['identifier']
        action_raw=response['llm_output']
        rst=evaluate_action_sequence_raw(demo_dir,action_raw,identifier,os.path.join(rst_dir,identifier+'.json'))
        output.append({
            "identifier":identifier,
            "llm_rst":rst
        })
        

    with open(os.path.join(rst_dir,file_name), 'w') as f:
        f.write(json.dumps(output,indent=4))

    return output

def get_summary(output,rst_dir,file_name='summary.json'):
    os.makedirs(rst_dir,exist_ok=True)
    summary={
            "error_type":{
            },
            "goal_rst":{
            },
        }
    for item in output:
        identifier=item['identifier']
        rst=item['llm_rst']
        for k,v in rst.items():
            if k in summary:
                if isinstance(v,dict):
                    for kk,vv in v.items():
                        if vv is not None:
                            if isinstance(vv,int) or isinstance(vv,float):
                                summary[k][kk]=summary[k].get(kk,0)+vv
                            elif isinstance(vv,bool):
                                summary[k][kk]=summary[k].get(kk,0)+int(vv)
                            else:
                                summary[k][kk]=summary[k].get(kk,0)+1

    with open(os.path.join(rst_dir,file_name), 'w') as f:
        json.dump(summary,f,indent=4)


def eval_one_llm_all(demo_dir,llm_response_path,rst_dir,llm_name):
    output=evaluate_llm_response_batch(demo_dir,llm_response_path,rst_dir,llm_name+'_rst.json')
    get_summary(output,rst_dir,llm_name+'_summary.json')

if __name__ == "__main__":
    fire.Fire(eval_one_llm_all)
    