import os
import json
import fire
from igibson.evaluation.transition_modeling.transition_modeling_evaluator import TransitionModelingEvaluator
from collections import defaultdict
def evaluate_transition_modeling(demo_dir,demo_name,output_dir):
    os.makedirs(output_dir,exist_ok=True)
    env=TransitionModelingEvaluator(demo_dir=demo_dir,demo_name=demo_name)
    actions=env.gold_actions
    with open(os.path.join(output_dir,'gold_actions.json'), 'w') as f:
        json.dump(actions,f,indent=4)
    

    


if __name__ == "__main__":
    fire.Fire(evaluate_transition_modeling)