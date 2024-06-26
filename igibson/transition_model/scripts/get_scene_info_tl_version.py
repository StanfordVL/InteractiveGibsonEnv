from igibson.transition_model.eval_env import EvalEnv
from igibson.transition_model.evaluation.action_sequence.action_sequence_evaluator import ActionSequenceEvaluator
from igibson.eval_subgoal_plan.tl_formula.bddl_to_tl import translate_bddl_final_states_into_tl, translate_bddl_final_states_into_simplified_tl
import platform
import json
import fire
import traceback
import os
import ast

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


def eval_manual_craft_prompt(demo_path, headless=True):
    env=ActionSequenceEvaluator(demo_path=demo_path)
    
    objects_str = env.get_objects().strip()
    initial_states_str = env.get_initial_state().strip()
    goal_states_str = env.get_target_state().strip()
    objects_in_scene = objects_str.split('\n')
    objects_in_scene = [ast.literal_eval(obj) for obj in objects_in_scene]
    initial_states = initial_states_str.split('\n')
    initial_states = [ast.literal_eval(state) for state in initial_states]
    goal_states = goal_states_str.split('\n')
    goal_states = [ast.literal_eval(state) for state in goal_states]

    tl_category_map = get_tl_category(objects_in_scene)

    print('Addressable Objects:')
    for obj in objects_in_scene:
        obj_name = obj['name']
        obj_category = obj['category']
        tl_obj_name = translate_addressable_obj_into_tl_obj(obj_name)
        tl_obj_category = tl_category_map[obj_category]
        tl_obj = {'name': tl_obj_name, 'category': tl_obj_category}
        print(tl_obj)
    print('-----------------------------------------------')
    print('Initial Conditions: ')
    for condition in initial_states:
        tl_condition = [translate_addressable_obj_into_tl_obj(obj) for obj in condition]
        primitive = tl_condition[0]
        tl_exp = f'{primitive}({", ".join(tl_condition[1:])})' if len(tl_condition) > 1 else primitive
        print(tl_exp)
    print('-----------------------------------------------')
    print('Goal Conditions: ')
    for condition in goal_states:
        tl_condition = []
        for obj in condition:
            if obj in tl_category_map:
                tl_condition.append(tl_category_map[obj])
            else:
                tl_condition.append(translate_addressable_obj_into_tl_obj(obj))
        print(tl_condition)
    
    # tl_goal_conditions = []
    # name_mapping = env.name_mapping
    # tl_goal_conditions = translate_bddl_final_states_into_tl(name_mapping, tl_category_map, env.task.goal_conditions, flatten=False)
    # print('-----------------------------------------------')
    # print('Translated LTL Goal Conditions:')
    # for condition in tl_goal_conditions:
    #     print(condition)
    

    # s_tl_goal_conditions = []
    # s_tl_goal_conditions = translate_bddl_final_states_into_simplified_tl(name_mapping, tl_category_map, env.task.goal_conditions)
    # print('-----------------------------------------------')
    # print('Simplified Translated LTL Goal Conditions:')
    # for condition in s_tl_goal_conditions:
    #     print(condition)
    # return

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
    t11 = 'assembling_gift_baskets_0_Beechwood_0_int_0_2021-10-26_12-46-37'
    task_list = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10]
    # task_list = [t11]
    return task_list

def main(demo_name='bottling_fruit_0_Wainscott_0_int_0_2021-05-24_19-46-46', demo_dir='./igibson/data/virtual_reality'):
    task_list = get_task_list()
    for task in task_list:
        # if task != 'filling_an_Easter_basket_0_Benevolence_1_int_1_2021-09-10_00-09-54':
        #     continue
        print('Running evaluation for task:', task)
        demo_path = os.path.join(demo_dir, task + '.hdf5')
        eval_manual_craft_prompt(demo_path)
        print('-----------------------------------------------')
        # exit()
    # print('Running evaluation for task:', demo_name)
    # demo_path = os.path.join(demo_dir, demo_name + '.hdf5')
    # eval_manual_craft_prompt(demo_path)
    ...

if __name__ == '__main__':
    fire.Fire(main)
