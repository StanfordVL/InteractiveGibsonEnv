import os
import ast
import json
import tqdm
import igibson
import argparse
from igibson.evaluation.action_sequence.action_sequence_evaluator import ActionSequenceEvaluator
from igibson.evaluation.eval_subgoal_plan.tl_formula.bddl_to_tl import translate_bddl_final_states_into_simplified_tl


def translate_addressable_obj_into_tl_obj(address_obj):
    if '_' not in address_obj:
        return address_obj
    address_obj = address_obj.replace('.', '_')
    parts = address_obj.split('_')
    assert len(parts) > 1, 'Invalid addressable object name: {}'.format(address_obj)
    tl_obj = '_'.join(parts[:-1]) + '.' + parts[-1]
    return tl_obj

def get_tl_category(obj_list):
    category_map = {}
    for obj in obj_list:
        category = obj['category']
        category_map[category] = category.replace('.', '_')
    return category_map


def convert_dict_to_list(dict_file_path, list_dict_path):
    with open(dict_file_path, 'r') as f:
        dict_data = json.load(f)
    list_data = []
    for task_name, task_info in dict_data.items():
        tmp = {
            "identifier": task_name,
            "llm_prompt": task_info['llm_prompt']
        }
        list_data.append(tmp)
    with open(list_dict_path, 'w') as f:
        json.dump(list_data, f, indent=4)


def generate_input_prompt(demo_name, demo_dir, prompt_components, log_path):
    if not os.path.exists(log_path):
        with open(log_path, 'w') as f:
            json.dump({}, f)
    with open(log_path, 'r') as f:
        logs = json.load(f)
    demo_path = os.path.join(demo_dir, demo_name + '.hdf5')
    if demo_name in logs:
        print(f'Demo {demo_name} has been processed before.')
        return
    env = ActionSequenceEvaluator(demo_path=demo_path)
    task_name = env.transition_model.config['task']
    objects_str = env.get_objects_str().strip()
    initial_states_str = env.get_initial_state().strip()
    goal_states_str = env.get_target_state().strip()
    objects_in_scene = objects_str.split('\n')
    objects_in_scene = [ast.literal_eval(obj) for obj in objects_in_scene]
    initial_states = initial_states_str.split('\n')
    initial_states = [ast.literal_eval(state) for state in initial_states]
    goal_states = goal_states_str.split('\n')
    goal_states = [ast.literal_eval(state) for state in goal_states]
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
    s_tl_goal_conditions = translate_bddl_final_states_into_simplified_tl(name_mapping, tl_category_map, env.task.goal_conditions)

    task_prompt = prompt_components['target_task']
    task_prompt = task_prompt.replace('<task_name>', task_name).replace('<relevant_objects>', '\n'.join(tl_objs)).replace('<initial_states>', '\n'.join(tl_exps)).replace('<goal_states>', '\n'.join(s_tl_goal_conditions))
    
    input_prompt = task_prompt
    logs[demo_name] = {
        "identifier": task_name,
        "llm_prompt": input_prompt
    }
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=4)
    return


def get_all_task_list():
    path = os.path.join(igibson.demo_name_path)
    with open(path, 'r') as f:
        task_list = json.load(f)
    return task_list

def get_test_task_list():
    t1 = 'cleaning_sneakers_0_Pomaria_1_int_0_2021-10-26_13-36-08'
    return [t1]


def main_generate_input_prompt(demo_name=None, demo_dir='./igibson/data/virtual_reality'):
    prompt_file_path = os.path.join(igibson.subgoal_prompt_root_path, 'subgoal_plan_final_prompt_behavior_meta.json')
    log_path = os.path.join(igibson.subgoal_prompt_root_path, 'subgoal_plan_final_input_prompt_with_name.json')
    with open(prompt_file_path, 'r') as f:
        prompt_components = json.load(f)
    task_list = get_all_task_list()
    total_num_tasks = len(task_list)
    faild_task_list = []
    for i, task in tqdm.tqdm(enumerate(task_list), desc="Processing tasks", unit="task", total=total_num_tasks):
        demo_name = task
        assert demo_name is not None, 'Please specify the demo name.'
        try:
            generate_input_prompt(demo_name, demo_dir, prompt_components, log_path)
        except Exception as e:
            print(f'Error in processing task {demo_name}: {e}')
            faild_task_list.append(demo_name)
            continue
    print('Statistics:')
    print(f'Total number of tasks: {total_num_tasks}')
    print(f'Number of failed tasks: {len(faild_task_list)}')
    print(f'Failed tasks:')
    for task in faild_task_list:
        print(task)


def main_convert():
    dict_file_path = os.path.join(igibson.subgoal_prompt_root_path, 'subgoal_plan_final_input_prompt_with_name.json')
    list_dict_path = os.path.join(igibson.subgoal_prompt_root_path, 'subgoal_plan_final_input_prompt_universal.json')
    convert_dict_to_list(dict_file_path, list_dict_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate input prompt and convert it.')
    parser.add_argument('--raw', action='store_true', help='Generate raw input prompt')
    parser.add_argument('--convert', action='store_true', help='Convert input prompt into helm form')
    parser.set_defaults(raw=True, convert=False)
    args = parser.parse_args()
    if args.convert:
        print('Call converting')
        main_convert()
    else:
        print('Call generating')
        main_generate_input_prompt()
