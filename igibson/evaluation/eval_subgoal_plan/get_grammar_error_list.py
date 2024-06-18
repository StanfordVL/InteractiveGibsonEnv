import json
import os
import ast

log_path = './igibson/evaluation/eval_subgoal_plan/error_list.json'

eval_base_path = './igibson/evaluation/eval_subgoal_plan/eval_stats'
pass_list = ['Correct', 'Runtime', 'GoalUnreachable']

log = {}

for root, dirs, files in os.walk(eval_base_path):
    for file in files:
        error_list = []
        eval_file_path = os.path.join(root, file)
        llm_name = file.replace('.json', '').replace('eval_', '')
        with open(eval_file_path, 'r') as f:
            eval_stats = json.load(f)

        for task_name, task_info in eval_stats.items():
            task_info = ast.literal_eval(task_info['info'])
            rst_type = task_info[0]
            if rst_type not in pass_list:
                error_list.append(task_name)
        log[llm_name] = error_list

with open(log_path, 'w') as f:
    json.dump(log, f, indent=4)
    

