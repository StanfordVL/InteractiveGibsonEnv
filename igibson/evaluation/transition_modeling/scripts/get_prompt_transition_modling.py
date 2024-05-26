import os
import json
import fire
from igibson.evaluation.transition_modeling.transition_modeling_evaluator import TransitionModelingEvaluator

def get_transition_modling_prompt(demo_dir,demo_name,rst_path):
    env=TransitionModelingEvaluator(demo_dir=demo_dir,demo_name=demo_name)
    prompt=env.get_prompt()
    rst={
        "identifier":demo_name,
        "llm_prompt":prompt,
    }
    with open(rst_path, 'w') as f:
        f.write(json.dumps(rst,indent=4))
    return rst
    
def main(demo_dir,demo_name,rst_path="test.json"):
    get_transition_modling_prompt(demo_dir,demo_name,rst_path)
if __name__ == "__main__":
    fire.Fire(main)