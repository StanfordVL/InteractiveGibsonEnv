from igibson.transition_model.eval_env import EvalActions
from igibson.transition_model.eval_env import EvalEnv
import platform
import io
from contextlib import redirect_stdout
import json
import fire
import traceback


binary_states=[
    'nextto',
    'ontop',
    'inside',
    'onfloor',
    'under',  
]


def evaluate_goal_condition_seqeunce(rst_path,save_path):
   
    
    with open(rst_path, 'r') as f:
        # read the result log file (not json format)
        file_contents = f.read()
        lines=file_contents.strip().split('\n')

    reading_goal_conditions = False
    goal_conditions = []
    for line in lines:
        if 'Goal Conditions:' in line:
            reading_goal_conditions = True
            continue

        if 'Action Execution Begins' in line:
            reading_goal_conditions = False
            break

        if reading_goal_conditions:
            goal_condition = eval(line.strip())
            goal_conditions.append(goal_condition)

    goal_types=[]
    for goal_condition in goal_conditions:
        edge_goal = False
        for relation in binary_states:
            if relation in goal_condition:
                goal_types.append('edge')
                edge_goal = True
                break
        if not edge_goal:
            goal_types.append('node')



    goal_rst=file_contents.split("Post Effects:")[-1]
    # get the index of the first '(' and ')' of the string
    start_idx = goal_rst.find('{')
    end_idx = goal_rst.find('}')
    goal_rst = eval(goal_rst[start_idx:end_idx+1])
    satisfied_goal_conditions = goal_rst['satisfied']

    rst={
        'total_goals': len(goal_conditions),
        'satisfied_goals': len(satisfied_goal_conditions),
        'edge_goals': sum([1 for goal_type in goal_types if goal_type == 'edge']),
        'node_goals': sum([1 for goal_type in goal_types if goal_type == 'node']),
        'satisfied_edge_goals': sum([1 for i in satisfied_goal_conditions if goal_types[i] == 'edge']),
        'satisfied_node_goals': sum([1 for i in satisfied_goal_conditions if goal_types[i] == 'node']),
    }
    with open(save_path, 'w') as f:
        json.dump(rst, f, indent=4)
    return rst

import os
def main(rst_path,save_path='test_rst.json'):
    evaluate_goal_condition_seqeunce(rst_path,save_path)
    
if __name__ == "__main__":
    fire.Fire(main)

