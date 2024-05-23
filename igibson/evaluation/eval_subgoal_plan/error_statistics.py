import os
import json
import ast
stats_file_path = './igibson/log/all_checking_gpt4.json'

with open(stats_file_path, 'r') as f:
    stats = json.load(f)

num_correct = 0
format_errors = 0
hallucination_errors = 0
runtime_errors = 0

incorrect_param_length_num = 0
obj_not_in_scene_num = 0

not_executable_num = 0

tot_runtime_errors = 0
missing_step_errors = 0
additional_step_errors = 0
affordance_errors = 0
wrong_temporal_order_errors = 0
for task, task_info in stats.items():
    success = task_info['success']
    if success:
        num_correct += 1
    info = task_info['info']
    assert info is not None, f'info is None for task {task}'
    info = ast.literal_eval(info)
    error_type = info[0]
    if error_type == 'format':
        format_errors += 1
    elif error_type == 'hallucination':
        hallucination_errors += 1
        error_dict = info[1]
        if not error_dict['IncorrectParamLength']:
            incorrect_param_length_num += 1
        if not error_dict['ObjectNotInScene']:
            obj_not_in_scene_num += 1
    elif error_type == 'runtime':
        runtime_errors += 1
        executable = info[1]
        if not executable:
            not_executable_num += 1
        runtime_report = info[2]
        for error in runtime_report:
            error_info = error['error_info']
            error_type = error_info['error_type']
            real_info = error_info['error_info']
            tot_runtime_errors += len(error_type)
            if len(error_type) >= 2:
                print(task, error_type)
            for t in error_type:
                if 'missing_step' in t.lower():
                    missing_step_errors += 1
                elif 'additional_step' in t.lower():
                    additional_step_errors += 1
                elif 'affordance' in t.lower():
                    affordance_errors += 1
                elif 'wrong_temporal_order' in t.lower():
                    wrong_temporal_order_errors += 1

    elif error_type == 'correct':
        runtime_report = info[3]
        for error in runtime_report:
            error_info = error['error_info']
            error_type = error_info['error_type']
            real_info = error_info['error_info']
            tot_runtime_errors += len(error_type)
            for t in error_type:
                if 'missing_step' in t.lower():
                    missing_step_errors += 1
                elif 'additional_step' in t.lower():
                    additional_step_errors += 1
                elif 'affordance' in t.lower():
                    affordance_errors += 1
                elif 'wrong_temporal_order' in t.lower():
                    wrong_temporal_order_errors += 1


tot_num = len(stats)

# print all stats
print('Total number of tasks:', tot_num)
print('Number of correct tasks:', num_correct)
print('Number of format errors:', format_errors)
print('Number of hallucination errors:', hallucination_errors)
print('Number of runtime errors:', runtime_errors)
print('Number of incorrect param length errors:', incorrect_param_length_num)
print('Number of obj not in scene errors:', obj_not_in_scene_num)
print('Number of not executable errors:', not_executable_num)
print('Number of total runtime errors:', tot_runtime_errors)
print('Number of missing step errors:', missing_step_errors)
print('Number of additional step errors:', additional_step_errors)
print('Number of affordance errors:', affordance_errors)
print('Number of wrong temporal order errors:', wrong_temporal_order_errors)


