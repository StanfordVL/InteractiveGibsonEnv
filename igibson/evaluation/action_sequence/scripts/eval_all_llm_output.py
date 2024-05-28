import subprocess
import sys
from multiprocessing import Process
import os
import fire
def eval_all_llm(demo_dir,llm_response_dir,rst_dir):
    os.makedirs(rst_dir,exist_ok=True)
    for filename in os.listdir(llm_response_dir):
        file_path = os.path.join(llm_response_dir, filename)
        model_name=filename.split('.json')[0]
        model_rst_dir=os.path.join(rst_dir,model_name)
        # Check if the path is a file
        if os.path.isfile(file_path):
            print(f"Processing file: {file_path}")
            # Call the a.py script with the required arguments
            result = subprocess.run(['python', 'evaluate_action_sequence.py', demo_dir, file_path, model_rst_dir,model_name], check=True, shell=True)
            if result.returncode != 0:
                print(f"Error processing file: {file_path}. Stopping.")
                break

if __name__ == '__main__':
    fire.Fire(eval_all_llm)