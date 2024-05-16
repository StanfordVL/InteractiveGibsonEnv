import openai
import os
import fire
import ast
import json
import tqdm
from igibson.utils.ig_logging import IGLogReader
from igibson.evaluation.action_sequence.action_sequence_evaluator import ActionSequenceEvaluator
from igibson.evaluation.eval_subgoal_plan.tl_formula.bddl_to_tl import translate_bddl_final_states_into_tl, translate_bddl_final_states_into_simplified_tl

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10809'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10809'
client = openai.OpenAI(api_key=os.environ.get('MANLING_OPENAI_KEY'))

def get_openai_output(messages:list, model="gpt-4-turbo", temperature=0.7, max_tokens=3500):
    isFail = False
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
    except openai.APITimeoutError as e:
        #Handle timeout error, e.g. retry or log
        print(f"OpenAI API request timed out: {e}")
        pass
    except openai.APIConnectionError as e:
        #Handle connection error, e.g. check network or log
        print(f"OpenAI API request failed to connect: {e}")
        pass
    except openai.AuthenticationError as e:
        #Handle authentication error, e.g. check credentials or log
        print(f"OpenAI API request was not authorized: {e}")
        pass
    except openai.BadRequestError as e:
        #Handle bad request error, e.g. check request body or log
        print(f"OpenAI API request was invalid: {e}")
        isFail = True
        pass
    except openai.PermissionDeniedError as e:
        #Handle permission error, e.g. check scope or log
        print(f"OpenAI API request was not permitted: {e}")
        pass
    except openai.RateLimitError as e:
        #Handle rate limit error, e.g. wait or log
        print(f"OpenAI API request exceeded rate limit: {e}")
        pass
    except Exception as e:
        #Handle other errors, e.g. log or raise
        print(f"OpenAI API request failed: {e}")
        isFail = True
        pass
    return completion.choices[0].message.content if not isFail else None

def translate_tl_obj_into_addressable_obj(tl_obj):
    addressable_obj = tl_obj.replace('.', '_')
    return addressable_obj

def translate_addressable_obj_into_tl_obj(address_obj):
    if '_' not in address_obj:
        return address_obj
    # replace the last char '_' with '.'
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


def eval_manual_craft_prompt(demo_path, prompt_components, log_path, headless=True):
    if not os.path.exists(log_path):
        with open(log_path, 'w') as f:
            json.dump({}, f)
    with open(log_path, 'r') as f:
        logs = json.load(f)

    task_name = IGLogReader.read_metadata_attr(demo_path, "/metadata/atus_activity")
    # if task_name in logs:
    #     # print(f'Task {task_name} has been processed before.')
    #     return
    env=ActionSequenceEvaluator(demo_path=demo_path)
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

    
    info_prompt = prompt_components['Background'] + prompt_components['StateInfo'] + prompt_components['SupplementInfo'] + "\n".join(prompt_components['GoldExamples'])
    task_prompt = prompt_components['TargetTask'].replace('<task_name>', task_name).replace('<relevant_objects>', '\n'.join(tl_objs)).replace('<initial_states>', '\n'.join(tl_exps)).replace('<goal_states>', '\n'.join(s_tl_goal_conditions))

    messages = [
        {"role": "system", "content": info_prompt},
        {"role": "user", "content": task_prompt}
    ]
    # print('Input:')
    # print(info_prompt + task_prompt)
    output = get_openai_output(messages)
    # print('Output:')
    # print(output)
    cur_log_info = {
        "input": info_prompt + task_prompt,
        "output": output
    }
    
    logs[task_name] = cur_log_info
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=4)
    return

def get_all_task_list():
    data_dir = './igibson/evaluation/data/action_sequence_human_annotations'
    task_list = []
    for file in os.listdir(data_dir):
        if file.endswith('.json'):
            task_list.append(file.replace('.json', ''))
    return task_list

def get_test_task_list():
    t1 = 'cleaning_sneakers_0_Pomaria_1_int_0_2021-10-26_13-36-08'
    return [t1]

def get_task_list():
    t1 = 'bottling_fruit_0_Wainscott_0_int_0_2021-05-24_19-46-46'
    t2 = 'cleaning_sneakers_0_Pomaria_1_int_0_2021-10-26_13-36-08'
    t3 = 'cleaning_up_after_a_meal_0_Wainscott_0_int_0_2021-10-20_05-33-24'
    t4 = 'cleaning_up_refrigerator_0_Wainscott_0_int_1_2021-06-23_17-46-01'
    t5 = 'filling_an_Easter_basket_0_Benevolence_1_int_1_2021-09-10_00-09-54'
    t6 = 'packing_picnics_0_Wainscott_0_int_0_2021-10-26_11-07-29'
    t7 = 'preparing_salad_0_Pomaria_1_int_1_2021-10-26_14-17-24'
    t8 = 'serving_a_meal_0_Merom_1_int_0_2021-10-26_00-34-17'
    t9 = 'serving_hors_d_oeuvres_0_Wainscott_0_int_0_2021-10-26_14-00-22'
    t10 = 'sorting_groceries_0_Wainscott_0_int_0_2021-10-26_13-36-01'

    # task_list = [t2, t3, t4, t5, t6, t7, t8, t9, t10]
    # task_list = [t8]
    task_list = [t1, t2, t3, t4, t5, t6, t7, t9, t10]
    return task_list

def main(demo_name=None, demo_dir='./igibson/data/virtual_reality'):
    prompt_file_path = 'F:\\Projects\\Research\\embodiedAI\\kangrui\\iGibson\\igibson\\eval_subgoal_plan\\resources\\subgoal_plan_prompt_s_ltl.json'
    log_path = 'F:\\Projects\\Research\\embodiedAI\\kangrui\\iGibson\\igibson\\eval_subgoal_plan\\resources\\log5-16-00.json'
    with open(prompt_file_path, 'r') as f:
        prompt_components = json.load(f)
    task_list = get_test_task_list()
    # task_list = get_all_task_list()
    total_num_tasks = len(task_list)
    faild_task_list = []
    for i, task in tqdm.tqdm(enumerate(task_list), desc="Processing tasks", unit="task", total=total_num_tasks):
        demo_name = task
        assert demo_name is not None, 'Please specify the demo name.'
        demo_path = os.path.join(demo_dir, demo_name + '.hdf5')
        try:
            eval_manual_craft_prompt(demo_path, prompt_components, log_path)
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

if __name__ == '__main__':
    fire.Fire(main)