import argparse
import json
import multiprocessing
import os
import ast
import igibson
from typing import Dict, Any, List, Union, Tuple
from igibson.evaluation.action_sequence.action_sequence_evaluator import ActionSequenceEvaluator
from igibson.evaluation.eval_subgoal_plan.tl_formula.bddl_to_tl import translate_addressable_obj_into_tl_obj, translate_raw_bddl_name_rep_into_tl_name_rep, build_simplified_tl_expr_from_bddl_condition_recursively, remove_redudant_list


counter = multiprocessing.Value('i', 0)
lock = multiprocessing.Lock()


def init_globals(cnt, lck):
    global counter
    global lock
    counter = cnt
    lock = lck

def get_tl_category(obj_list):
    category_map = {}
    for obj in obj_list:
        category = obj['category']
        category_map[category] = category.replace('.', '_')
    return category_map

def generate_input_prompt(demo_dir:str, task_name, task_info, task_prompt:str, log_path:str, llm_name:str):
    demo_path = os.path.join(demo_dir, task_name + '.hdf5')
    env = ActionSequenceEvaluator(demo_path=demo_path)

    formal_task_name = env.transition_model.config['task']
    objects_str = env.get_objects_str().strip()
    initial_states_str = env.get_initial_state().strip()
    objects_in_scene = objects_str.split('\n')
    objects_in_scene = [ast.literal_eval(obj) for obj in objects_in_scene]
    initial_states = initial_states_str.split('\n')
    initial_states = [ast.literal_eval(state) for state in initial_states]
    name_mapping = env.name_mapping

    tl_category_map = get_tl_category(objects_in_scene)
    tl_objs = []
    for obj in objects_in_scene:
        obj_name = obj['name']
        obj_category = obj['category']
        tl_obj_name = translate_addressable_obj_into_tl_obj(obj_name)
        tl_obj_category = tl_category_map[obj_category]
        tl_obj = {'name': tl_obj_name, 'category': tl_obj_category}
        tl_objs.append(str(tl_obj))
    tl_exps = []
    for condition in initial_states:
        tl_condition = [translate_addressable_obj_into_tl_obj(obj) for obj in condition]
        primitive = tl_condition[0]
        if primitive == 'not':
            next_primitive = tl_condition[1]
            tl_exp = f'{next_primitive}({", ".join(tl_condition[2:])})' if len(tl_condition) > 2 else next_primitive
            tl_exp = f'not {tl_exp}'
        else:
            tl_exp = f'{primitive}({", ".join(tl_condition[1:])})' if len(tl_condition) > 1 else primitive
        tl_exps.append(tl_exp)

    s_tl_goal_conditions = []
    for node_condition in task_info['node goals']:
        node_condition = remove_redudant_list(node_condition)
        translated_condition = translate_raw_bddl_name_rep_into_tl_name_rep(name_mapping, tl_category_map, node_condition)
        simplified_tl_expr = build_simplified_tl_expr_from_bddl_condition_recursively(translated_condition)
        s_tl_goal_conditions.append(simplified_tl_expr)
    for edge_condition in task_info['edge goals']:
        edge_condition = remove_redudant_list(edge_condition)
        if isinstance(edge_condition[1][0], List):
            edge_condition[1:] = edge_condition[1]
        translated_condition = translate_raw_bddl_name_rep_into_tl_name_rep(name_mapping, tl_category_map, edge_condition)
        simplified_tl_expr = build_simplified_tl_expr_from_bddl_condition_recursively(translated_condition)
        s_tl_goal_conditions.append(simplified_tl_expr)

    task_prompt = task_prompt.replace('<task_name>', formal_task_name).replace('<relevant_objects>', '\n'.join(tl_objs)).replace('<initial_states>', '\n'.join(tl_exps)).replace('<goal_states>', '\n'.join(s_tl_goal_conditions))
    result = {
        'identifier': task_name,
        'llm_prompt': task_prompt,
    }
    with lock:
        counter.value += 1
        with open(log_path, 'r') as f:
            log = json.load(f)
        log[llm_name].append(result)
        with open(log_path, 'w') as f:
            json.dump(log, f, indent=4)
        print(f'Current total: {counter.value}')


def find_task(task_name:str, logs:List[Dict[str, str]]) -> bool:
    for log in logs:
        if log['identifier'] == task_name:
            return True
    return False
    ...

def get_real_task_list(llm_results:Dict[str, Any], log_path:str, llm_name:str):
    with open(log_path, 'r') as f:
        logs = json.load(f)
    llm_logs = logs[llm_name]
    task_list = []
    for task_name, task_info in llm_results.items():
        if not find_task(task_name, llm_logs):
            task_list.append((task_name, task_info))
    return task_list

def get_initial_log_dict(goal_results) -> Dict[str, List]:
    log_dict = {}
    for llm_name, tasks in goal_results.items():
        log_dict[llm_name] = []
    return log_dict

def get_generated_len():
    log_path = './igibson/evaluation/eval_subgoal_plan/goal_inter_and_subgoal/resources/all_goal_intr_and_subgoal_prompts.json'
    goal_interpret_path = './igibson/evaluation/eval_subgoal_plan/goal_inter_and_subgoal/resources/all_behavior_goal_interpretation_outputs.json'
    with open(goal_interpret_path, 'r') as f:
        goal_results = json.load(f)
    log_path = './igibson/evaluation/eval_subgoal_plan/goal_inter_and_subgoal/resources/all_goal_intr_and_subgoal_prompts.json'
    with open(log_path, 'r') as f:
        logs = json.load(f)
    for llm_name, tasks in logs.items():
        llm_results = goal_results[llm_name]
        real_task_list = get_real_task_list(llm_results, log_path, llm_name)
        if len(tasks) != 100:
            print(f'{llm_name}: {len(tasks)}')
            print([task for task, _ in real_task_list])
    
    ...


def main_generate_input_prompt(input_llm_name:str, n_proc:int, task_num:int):
    demo_dir = './igibson/data/virtual_reality'
    prompt_file_path = './igibson/evaluation/eval_subgoal_plan/goal_inter_and_subgoal/resources/goal_intepret_subgoal_plan_final_prompt_behavior_meta.json'
    log_path = './igibson/evaluation/eval_subgoal_plan/goal_inter_and_subgoal/resources/all_goal_intr_and_subgoal_prompts.json'
    goal_interpret_path = './igibson/evaluation/eval_subgoal_plan/goal_inter_and_subgoal/resources/all_behavior_goal_interpretation_outputs.json'
    with open(prompt_file_path, 'r') as f:
        prompt_components = json.load(f)
    user_prompt = prompt_components["target_task"]
    with open(goal_interpret_path, 'r') as f:
        goal_results = json.load(f)
    llm_results = goal_results[input_llm_name]
    if not os.path.exists(log_path):
        init_log = get_initial_log_dict(goal_results)
        with open(log_path, 'w') as f:
            json.dump(init_log, f, indent=4)
    real_task_list = get_real_task_list(llm_results, log_path, input_llm_name)

    print(f'llm_name: {input_llm_name}')
    if len(real_task_list) == 0:
        print('All tasks have been generated')
        return
    print(f'remaining tasks: {len(real_task_list)}')
    real_task_list = real_task_list[:task_num] if len(real_task_list) > task_num else real_task_list

    n_proc = min(multiprocessing.cpu_count(), len(real_task_list), n_proc)
    print(f'Number of processes: {n_proc}')
    print(f'Total tasks: {len(real_task_list)}')
    with multiprocessing.Pool(processes=n_proc, initializer=init_globals, initargs=(counter, lock)) as pool:
        try:
            pool.starmap(generate_input_prompt, [(demo_dir, task_name, task_info, user_prompt, log_path, llm_name) for task_name, task_info in real_task_list])
        except Exception as e:
            print(e)
            pool.terminate()
        finally:
            pool.close()
            pool.join()

def run_one_case(input_llm_name:str, task_name: str):
    demo_dir = './igibson/data/virtual_reality'
    prompt_file_path = './igibson/evaluation/eval_subgoal_plan/goal_inter_and_subgoal/resources/goal_intepret_subgoal_plan_final_prompt_behavior_meta.json'
    log_path = './igibson/evaluation/eval_subgoal_plan/goal_inter_and_subgoal/resources/all_goal_intr_and_subgoal_prompts.json'
    goal_interpret_path = './igibson/evaluation/eval_subgoal_plan/goal_inter_and_subgoal/resources/all_behavior_goal_interpretation_outputs.json'
    with open(prompt_file_path, 'r') as f:
        prompt_components = json.load(f)
    user_prompt = prompt_components["target_task"]
    with open(goal_interpret_path, 'r') as f:
        goal_results = json.load(f)
    llm_results = goal_results[input_llm_name]
    task_info = llm_results[task_name]
    generate_input_prompt(demo_dir, task_name, task_info, user_prompt, log_path, input_llm_name)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate subgoal plan')
    parser.add_argument('--llm_name', type=str,  default='gpt-4-turbo-2024-04-09', help='Name of the LLM')
    parser.add_argument('--n_proc', type=int, default=5, help='Number of processes')
    parser.add_argument('--max_tasks', type=int, default=100, help='Number of tasks to generate')
    args = parser.parse_args()
    llm_name = args.llm_name.replace('_outputs', '')
    n_proc = args.n_proc
    task_num = args.max_tasks
    
    main_generate_input_prompt(llm_name, n_proc, task_num)
    # run_one_case('cohere-command-r-plus', 'putting_up_Christmas_decorations_inside_0_Ihlen_1_int_0_2021-06-03_14-27-09')
    # get_generated_len()