import os
import json
import fire
from igibson.evaluation.utils.gpt_utils import call_gpt_with_retry

def main(prompt_path,rst_dir):
    os.makedirs(rst_dir,exist_ok=True)
    prompt_list=json.load(open(prompt_path))
    output=[]
    for prompt in prompt_list:
        identifier=prompt['identifier']
        llm_prompt=prompt['llm_prompt']
        response=call_gpt_with_retry(llm_prompt)
        output_dict={
            "identifier":identifier,
            "llm_output":response,
        }
        output.append(output_dict)
        with open(os.path.join(rst_dir,'llm_result.json'), 'w') as f:
            f.write(json.dumps(output,indent=4))


    with open(os.path.join(rst_dir,'llm_result.json'), 'w') as f:
        f.write(json.dumps(output,indent=4))
    

if __name__ == "__main__":
    fire.Fire(main)
