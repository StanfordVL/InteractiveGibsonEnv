import os
import json
import ast
import argparse
import time

def get_eval_list(mode):
    if mode == 'single':
        eval_path = os.path.join('./igibson/evaluation/eval_subgoal_plan/', 'single_module', 'eval_stats')
    elif mode == 'pipeline':
        eval_path = os.path.join('./igibson/evaluation/eval_subgoal_plan/', 'goal_inter_and_subgoal', 'eval_stats')
    path_list = []
    for parent, dirnames, filenames in os.walk(eval_path):
        for filename in filenames:
            path_list.append(os.path.join(parent, filename))
    return path_list


def run_error_eval(mode):
    path_list = get_eval_list(mode)
    cur_time_h_m_s = time.strftime('%H-%M-%S', time.localtime(time.time()))
    log_file_path = os.path.join('./igibson/evaluation/eval_subgoal_plan/', 'logs', mode, f'trajectory_statistics_{cur_time_h_m_s}.log')

    # mkdirs for log_file_path
    log_dir = os.path.dirname(log_file_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    with open(log_file_path, 'w') as f:
        f.write(f'Trajectory statistics for {mode} evaluation\n\n')
        for stats_file_path in path_list:
            back_str = '\\'
            model_name = stats_file_path.split(back_str)[-1].replace('.json', '')
            f.write(f'[{model_name}]\n')
            with open(stats_file_path, 'r') as f2:
                stats = json.load(f2)

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
            f.write(f'Correct tasks rate: {num_correct/tot_num*100:.2f}%\n')
            f.write(f'Executable rate: {executable_num/tot_num*100:.2f}%\n')
            f.write(f'Parse errors rate: {parse_errors/tot_num*100:.2f}%\n')
            f.write(f'Hallucination errors rate: {(hallucination_errors-incorrect_param_length_num)/tot_num*100:.2f}%\n')
            f.write(f'Incorrect param length errors rate: {incorrect_param_length_num/tot_num*100:.2f}%\n')
            f.write(f'Wrong temporal order errors rate: {wrong_temporal_order_errors/tot_num*100:.2f}%\n')
            f.write(f'Missing step errors rate: {missing_step_errors/tot_num*100:.2f}%\n')
            f.write(f'Affordance errors rate: {affordance_errors/tot_num*100:.2f}%\n')
            f.write(f'Additional step errors rate: {additional_step_errors/tot_num*100:.2f}%\n')
            f.write('\n')





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Trajectory evaluation for subgoal decomposition')
    parser.add_argument('--single', action='store_true', help='Evaluate a single module of subgoal decomposition')
    parser.add_argument('--pipeline', action='store_true', help='Evaluate the whole pipeline of goal interpretation and subgoal decomposition')
    parser.set_defaults(single=True, pipeline=False)
    args = parser.parse_args()

    if args.pipeline:
        print('Evaluating the whole pipeline')
        mode = 'pipeline'
    else:
        print('Evaluating the single module')
        mode = 'single'
    
    run_error_eval(mode)