import os
import json
import fire
from action_sequence_evaluator import ActionSequenceEvaluator

def get_llm_action_seqeunce(demo_path,rst_path):
    env=ActionSequenceEvaluator(demo_path=demo_path)
    prompt=env.get_prompt_zeroshot()
    raw_response=env.get_raw_response(prompt)
    print(raw_response)
    response=env.parse_response(raw_response)
    print(response)
    with open(rst_path, 'w') as f:
        f.write(json.dumps(response,indent=4))
    return {
        "response":response,
        "raw_response":raw_response
    }
    
def main(demo_name,demo_dir="./igibson/data/virtual_reality",rst_path="test.json"):
    demo_path=os.path.join(demo_dir,demo_name)
    get_llm_action_seqeunce(demo_path,rst_path)
if __name__ == "__main__":
    fire.Fire(main)
"""
python D:\GitHub\behavior-vllm-eval\igibson\transition_model_v3\evaluation\action_sequence\get_llm_action_sequence.py "D:\GitHub\behavior-vllm-eval\igibson\data\virtual_reality\bottling_fruit_0_Wainscott_0_int_0_2021-05-24_19-46-46.hdf5"
"""

