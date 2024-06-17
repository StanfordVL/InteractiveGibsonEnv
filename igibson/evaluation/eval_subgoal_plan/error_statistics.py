import os
import json
import ast

def get_eval_list():
    # eval_path = './igibson/evaluation/eval_subgoal_plan/goal_inter_and_subgoal/eval_stats' # goal interpret + subgoal decomposition
    eval_path = './igibson/evaluation/eval_subgoal_plan/eval_stats' # goal interpret + subgoal decomposition
    path_list = []
    for parent, dirnames, filenames in os.walk(eval_path):
        for filename in filenames:
            path_list.append(os.path.join(parent, filename))
    return path_list

path_list = get_eval_list()

# stats_file_path = './igibson/evaluation/eval_subgoal_plan/eval_stats/' + 'eval_mixtral-8x22b-instruct-v0.1' + '.json'

for stats_file_path in path_list:
    print()
    print(f'=={stats_file_path.split("/")[-1]}==')
    print()
    with open(stats_file_path, 'r') as f:
        stats = json.load(f)

    num_correct = 0
    parse_errors = 0
    hallucination_errors = 0
    runtime_errors = 0
    goal_errors = 0

    incorrect_param_length_num = 0
    obj_not_in_scene_num = 0
    unknown_primitive_num = 0

    executable_num = 0

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
        if error_type == 'NotParseable' or error_type == 'Hallucination':
            if error_type == 'NotParseable':
                parse_errors += 1
            elif error_type == 'Hallucination':
                hallucination_errors += 1
                error_dict = info[1]
                if 'error_type' in error_dict and error_dict['error_type'] == 'UnknownPrimitive':
                    unknown_primitive_num += 1
                else:
                    if not error_dict['IncorrectParamLength']:
                        incorrect_param_length_num += 1
                    if not error_dict['ObjectNotInScene']:
                        obj_not_in_scene_num += 1
        elif error_type == 'GoalUnreachable':
            goal_errors += 1
            executable_num += 1
        
        else:
            if error_type == 'Runtime':
                runtime_errors += 1
                executable = info[1]
                if executable:
                    executable_num += 1
            else:
                executable_num += 1
            runtime_report = info[-1]
            get_one_additional = False
            for error in runtime_report:
                error_info = error['error_info']
                error_type = error_info['error_type']
                real_info = error_info['error_info']
                tot_runtime_errors += len(error_type)
                for t in error_type:
                    if 'missing_step' in t.lower():
                        missing_step_errors += 1
                    elif 'additional_step' in t.lower():
                        if not get_one_additional:
                            additional_step_errors += 1
                            get_one_additional = True
                    elif 'affordance' in t.lower():
                        affordance_errors += 1
                    elif 'wrong_temporal_order' in t.lower():
                        wrong_temporal_order_errors += 1


    tot_num = len(stats)
    print(f'Correct tasks rate: {num_correct/tot_num*100:.2f}%')
    print(f'Executable rate: {executable_num/tot_num*100:.2f}%')
    # print(f'Incorrect tasks rate: {(tot_num - num_correct)/tot_num*100:.2f}%')
    print(f'Parse errors rate: {parse_errors/tot_num*100:.2f}%')
    print(f'Hallucination errors rate: {(hallucination_errors-incorrect_param_length_num)/tot_num*100:.2f}%')
    print(f'Incorrect param length errors rate: {incorrect_param_length_num/tot_num*100:.2f}%')
    # print(f'Runtime errors rate: {runtime_errors/tot_num*100:.2f}%')
    # print(f'Goal errors rate: {goal_errors/tot_num*100:.2f}%')
    # print(f'Obj not in scene errors rate: {obj_not_in_scene_num/tot_num*100:.2f}%')
    # print(f'Unknown primitive errors rate: {unknown_primitive_num/tot_num*100:.2f}%')
    # print(f'Total runtime errors rate: {tot_runtime_errors/tot_num*100:.2f}%')
    print(f'Wrong temporal order errors rate: {wrong_temporal_order_errors/tot_num*100:.2f}%')
    print(f'Missing step errors rate: {missing_step_errors/tot_num*100:.2f}%')
    print(f'Affordance errors rate: {affordance_errors/tot_num*100:.2f}%')
    print(f'Additional step errors rate: {additional_step_errors/tot_num*100:.2f}%')
# print all stats
# print('Total number of tasks:', tot_num)
# print('Number of correct tasks:', num_correct)
# print('Number of incorrect tasks:', tot_num - num_correct)
# print('Number of parse errors:', parse_errors)
# print('Number of hallucination errors:', hallucination_errors-incorrect_param_length_num)
# print('Number of incorrect param length errors:', incorrect_param_length_num)
# print('Number of runtime errors:', runtime_errors)
# print('Number of goal errors:', goal_errors)
# print()
# print('Number of executable num:', executable_num)
# print('Number of obj not in scene errors:', obj_not_in_scene_num)
# print('Number of unknown primitive errors:', unknown_primitive_num)
# print('Number of total runtime errors:', tot_runtime_errors)
# print('Number of missing step errors:', missing_step_errors)
# print('Number of additional step errors:', additional_step_errors)
# print('Number of affordance errors:', affordance_errors)
# print('Number of wrong temporal order errors:', wrong_temporal_order_errors)






# format_errors = 0
# hallucination_errors = 0
# runtime_errors = 0

# incorrect_param_length_num = 0
# obj_not_in_scene_num = 0

# executable_num = 0

# tot_runtime_errors = 0
# missing_step_errors = 0
# additional_step_errors = 0
# affordance_errors = 0
# wrong_temporal_order_errors = 0
# for task, task_info in stats.items():
#     success = task_info['success']
#     if success:
#         num_correct += 1
#     info = task_info['info']
#     assert info is not None, f'info is None for task {task}'
#     info = ast.literal_eval(info)
#     error_type = info[0]
#     if error_type == 'format':
#         format_errors += 1
#     elif error_type == 'hallucination':
#         hallucination_errors += 1
#         error_dict = info[1]
#         if not error_dict['IncorrectParamLength']:
#             incorrect_param_length_num += 1
#         if not error_dict['ObjectNotInScene']:
#             obj_not_in_scene_num += 1
#     elif error_type == 'runtime':
#         runtime_errors += 1
#         executable = info[1]
#         if not executable:
#             executable_num += 1
#         runtime_report = info[2]
#         for error in runtime_report:
#             error_info = error['error_info']
#             error_type = error_info['error_type']
#             real_info = error_info['error_info']
#             tot_runtime_errors += len(error_type)
#             if len(error_type) >= 2:
#                 print(task, error_type)
#             for t in error_type:
#                 if 'missing_step' in t.lower():
#                     missing_step_errors += 1
#                 elif 'additional_step' in t.lower():
#                     additional_step_errors += 1
#                 elif 'affordance' in t.lower():
#                     affordance_errors += 1
#                 elif 'wrong_temporal_order' in t.lower():
#                     wrong_temporal_order_errors += 1

#     elif error_type == 'correct':
#         runtime_report = info[3]
#         for error in runtime_report:
#             error_info = error['error_info']
#             error_type = error_info['error_type']
#             real_info = error_info['error_info']
#             tot_runtime_errors += len(error_type)
#             for t in error_type:
#                 if 'missing_step' in t.lower():
#                     missing_step_errors += 1
#                 elif 'additional_step' in t.lower():
#                     additional_step_errors += 1
#                 elif 'affordance' in t.lower():
#                     affordance_errors += 1
#                 elif 'wrong_temporal_order' in t.lower():
#                     wrong_temporal_order_errors += 1


# tot_num = len(stats)

# # print all stats
# print('Total number of tasks:', tot_num)
# print('Number of correct tasks:', num_correct)
# print('Number of format errors:', format_errors)
# print('Number of hallucination errors:', hallucination_errors)
# print('Number of runtime errors:', runtime_errors)
# print('Number of incorrect param length errors:', incorrect_param_length_num)
# print('Number of obj not in scene errors:', obj_not_in_scene_num)
# print('Number of not executable errors:', executable_num)
# print('Number of total runtime errors:', tot_runtime_errors)
# print('Number of missing step errors:', missing_step_errors)
# print('Number of additional step errors:', additional_step_errors)
# print('Number of affordance errors:', affordance_errors)
# print('Number of wrong temporal order errors:', wrong_temporal_order_errors)


