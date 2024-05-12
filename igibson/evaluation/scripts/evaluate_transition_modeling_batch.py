import os
import json
import fire
from igibson.evaluation.transition_modeling.transition_modeling_evaluator import TransitionModelingEvaluator
from collections import defaultdict
def evaluate_transition_modeling(demo_dir,demo_name,llm_response):
    env=TransitionModelingEvaluator(demo_dir=demo_dir,demo_name=demo_name)
    parsed_llm_response=env.parse_response(llm_response)
    return env.compute_score(parsed_llm_response)
    
    
def main(demo_dir,responses_path,rst_dir):
    with open(responses_path, 'r') as f:
        responses = json.load(f)
    summary=defaultdict(dict)
    for response in responses:
        demo_name=response['identifier']
        llm_response=response['llm_output']
        score_dict=evaluate_transition_modeling(demo_dir,demo_name,llm_response)
        for k,v in score_dict.items():
            response[k]=v
            if k not in summary:
                summary[k]['precondition_score']=[]
                summary[k]['effect_score']=[]
            summary[k]['precondition_score'].append(v['precondition_score'])
            summary[k]['effect_score'].append(v['effect_score'])
                
        for k,v in summary.items():
            summary[k]['precondition_score_avg']=sum(v['precondition_score'])/len(v['precondition_score'])
            summary[k]['effect_score_avg']=sum(v['effect_score'])/len(v['effect_score'])

        with open(os.path.join(rst_dir,'llm_result_eval.json'), 'w') as f:
            f.write(json.dumps(responses,indent=4))
        with open(os.path.join(rst_dir,'summary.json'), 'w') as f:
            f.write(json.dumps(summary,indent=4))
    avg_summary=defaultdict(dict)
    for k,v in summary.items():
        avg_summary[k]['precondition_score_avg']=v['precondition_score_avg']
        avg_summary[k]['effect_score_avg']=v['effect_score_avg']
    with open(os.path.join(rst_dir,'avg_summary.json'), 'w') as f:
        f.write(json.dumps(avg_summary,indent=4))

    


if __name__ == "__main__":
    fire.Fire(main)