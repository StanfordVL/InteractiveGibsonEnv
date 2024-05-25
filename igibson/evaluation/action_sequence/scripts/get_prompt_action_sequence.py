import os
import json
import fire
from igibson.evaluation.action_sequence.action_sequence_evaluator import ActionSequenceEvaluator

def get_llm_prompt(demo_path,rst_path):
    env=ActionSequenceEvaluator(demo_path=demo_path)
    prompt=env.get_prompt()
    demo_name=demo_path.split("\\")[-1].replace(".hdf5","")
    rst={
        "identifier":demo_name,
        "llm_prompt":prompt,
    }
    with open(rst_path, 'w') as f:
        f.write(json.dumps(rst,indent=4))
    return rst
    
def main(demo_name,demo_dir="./igibson/data/virtual_reality",rst_path="test.json"):
    demo_path=os.path.join(demo_dir,demo_name)
    get_llm_prompt(demo_path,rst_path)
if __name__ == "__main__":
    fire.Fire(main)