import contextlib
import json
import os
import random

from igibson.evolving_graph.eval_evolving_graph_env import EvalGraphEnv
from igibson.tasks.behavior_task import BehaviorTask
from typing import List, Dict, Any, Optional, Tuple, Union
from igibson.evaluation.eval_subgoal_plan.subgoal_plan import SubgoalPlan, SubgoalPlanJSON, SubgoalPlanPlain
from igibson.evaluation.eval_subgoal_plan.checkers import Vocab, SyntacticChecker, SemanticChecker, RuntimeChecker
from igibson.evaluation.eval_subgoal_plan.state_action_translator import StateActionTranslator
from igibson.evaluation.eval_subgoal_plan.tl_formula.bddl_to_tl import translate_addressable_obj_into_tl_obj, translate_tl_obj_into_addressable_obj
import io
import sys
import multiprocessing

class EvalStatistics:
    def __init__(self, task_list: List[str], log_path: str) -> None:
        self.task_list = task_list
        self.log_path = log_path
        self.eval_rst_dict = self.init_eval_rst_dict()
    
    def init_eval_rst_dict(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.log_path):
            with open(self.log_path, 'r') as f:
                eval_dict = json.load(f)
            return eval_dict
        
        eval_dict = {}
        for task_name in self.task_list:
            eval_dict[task_name] = {
                'success': False,
                'info': None
            }
        return eval_dict
    
    def update_eval_rst_dict(self, task_name:str, success:bool, error_info:Union[str, None]):
        self.eval_rst_dict[task_name]['success'] = success
        self.eval_rst_dict[task_name]['info'] = error_info
    
    def get_eval_rst_dict(self) -> Dict[str, Dict[str, Any]]:
        return self.eval_rst_dict
    
    def check_evaluated_task(self, task_name:str) -> bool:
        if self.eval_rst_dict[task_name]['success'] == False and self.eval_rst_dict[task_name]['info'] is None:
            return False
        return True
    
    def save_eval_rst_dict(self):
        with open(self.log_path, 'w') as f:
            json.dump(self.eval_rst_dict, f, indent=4)


class EvalSubgoalPlan:
    def __init__(self, demo_path:str, plan_path:str, json_format:Optional[bool]=False) -> None:
        self.env = EvalGraphEnv(demo_path=demo_path)
        self.igibson_name_mapping = self.env.get_name_mapping()
        self.igibson_relevant_objects = self.env.get_relevant_obj_list(self.igibson_name_mapping)
        self.category_map = self.get_tl_category(self.igibson_name_mapping) #type:ignore
        self.tl_name_mapping = self.get_tl_name_mapping(self.igibson_name_mapping, self.category_map) #type:ignore
        self.tl_relevant_objects = [obj['name'] for obj in self.tl_name_mapping]
        self.task_name = self.env.task.behavior_activity #type:ignore
        self.subgoal_plan = SubgoalPlanPlain(plan_path, self.task_name) if not json_format else SubgoalPlanJSON(plan_path, self.task_name)
    
    def get_tl_category(self, igibson_name_mapping:List[Dict[str, str]]) -> Dict[str, str]:
        category_map = {}
        for pair in igibson_name_mapping:
            category = pair['category']
            category_map[category] = category.replace('.', '_')
        return category_map


    def get_tl_name_mapping(self, igibson_name_mapping:List[Dict[str, str]], category_map: Dict[str, str]) -> List[Dict[str, str]]:
        tl_name_mapping = []
        for pair in igibson_name_mapping:
            obj_name = pair['name']
            obj_category = pair['category']
            tl_obj_name = translate_addressable_obj_into_tl_obj(obj_name)
            tl_obj_category = category_map[obj_category]
            tl_obj = {'name': tl_obj_name, 'category': tl_obj_category}
            tl_name_mapping.append(tl_obj)
        return tl_name_mapping
    
    def evaluate_subgoal_plan(self):
        vocab = Vocab(self.tl_name_mapping, self.tl_relevant_objects)
        syntactic_checker = SyntacticChecker(self.subgoal_plan, vocab)
        syntactic_rst = syntactic_checker.run_result
        if not syntactic_rst:
            syntactic_report = syntactic_checker.report()
            error_tuple = ('format', syntactic_report)
            return error_tuple
        tl_expression = syntactic_checker.get_parsed_tl_expression()
        semantic_checker = SemanticChecker(self.subgoal_plan, vocab, tl_expression, True)
        semantic_rst = semantic_checker.run_result
        if not semantic_rst:
            semantic_report = semantic_checker.report()
            error_tuple = ('hallucination', semantic_report)
            return error_tuple
        runtime_checker = RuntimeChecker(self.env, self.subgoal_plan, vocab, tl_expression, True)
        runtime_report = runtime_checker.report()
        runtime_rst = runtime_checker.run_result
        if not runtime_rst:
            error_tuple = ('runtime', runtime_checker.executable, runtime_report)
            return error_tuple
        return ('correct', runtime_checker.executable, runtime_checker.feasible_action_seqs, runtime_report)
        

    # def evaluate_first_two_part(self):
    #     vocab = Vocab(self.tl_name_mapping, self.tl_relevant_objects)
    #     syntactic_checker = SyntacticChecker(self.subgoal_plan, vocab)
    #     syntactic_rst = syntactic_checker.run_result
    #     if not syntactic_rst:
    #         syntactic_report = syntactic_checker.report()
    #         error_tuple = ('syntax', syntactic_report)
    #         return error_tuple
    #     tl_expression = syntactic_checker.get_parsed_tl_expression()
    #     semantic_checker = SemanticChecker(self.subgoal_plan, vocab, tl_expression, True)
    #     semantic_rst = semantic_checker.run_result
    #     if not semantic_rst:
    #         semantic_report = semantic_checker.report()
    #         error_tuple = ('semantic', semantic_report)
    #         return error_tuple
    #     runtime_checker = RuntimeChecker(self.env, self.subgoal_plan, vocab, tl_expression, True)
    #     print(self.subgoal_plan)
    #     # runtime_checker.test_state_action_translator()
    #     # print(tl_expression)
    #     # runtime_checker.print_det_subgoal_tl_list()


def get_all_task_list():
    data_dir = './igibson/evaluation/data/action_sequence_human_annotations'
    task_list = []
    for file in os.listdir(data_dir):
        if file.endswith('.json'):
            task_list.append(file.replace('.json', ''))
    return task_list

def get_test_task_list():
    t1 = 'cleaning_cupboards_0_Wainscott_1_int_1_2021-08-25_16-40-44'
    return [t1]

counter = multiprocessing.Value('i', 0)
lock = multiprocessing.Lock()


def init_globals(cnt, lck):
    global counter
    global lock
    counter = cnt
    lock = lck

def evaluate_task(task_name, demo_dir, plan_path, eval_stat_path, test_mode=False):
    global lock
    global counter
    demo_path = os.path.join(demo_dir, task_name + '.hdf5')
    eval_subgoal_plan = EvalSubgoalPlan(demo_path, plan_path)
    report = eval_subgoal_plan.evaluate_subgoal_plan()
    # eval_subgoal_plan.test_eval_graph_env()
    if test_mode == True:
        return report
    with lock:
        counter.value += 1
        print(f'Current task number: {counter.value}')
        eval_statistics = EvalStatistics(get_all_task_list(), eval_stat_path)
        if report[0] != 'correct':
            eval_statistics.update_eval_rst_dict(task_name, False, str(report))
        else:
            eval_statistics.update_eval_rst_dict(task_name, True, str(report))
        eval_statistics.save_eval_rst_dict()
    return report

def eval_subgoal_plan():
    demo_dir = './igibson/data/virtual_reality'
    plan_path = './igibson/evaluation/eval_subgoal_plan/resources/log5-16-00.json'
    task_list = get_all_task_list()
    eval_stat_path = './igibson/log/all_checking_gpt4.json'
    eval_statistics = EvalStatistics(task_list, eval_stat_path)
    real_task_list = [task_name for task_name in task_list if not eval_statistics.check_evaluated_task(task_name)]
    real_task_list = real_task_list[:12] if len(real_task_list) > 12 else real_task_list
    print(len(real_task_list))

    n_proc = min(multiprocessing.cpu_count(), len(real_task_list), 6)
    
    with multiprocessing.Pool(processes=n_proc, initializer=init_globals, initargs=(counter, lock)) as pool:
        eval_stat_path = eval_stat_path
        # Pass only the task name, other arguments are inherited from the global context
        try:
            results = [pool.apply_async(evaluate_task, (task_name, demo_dir, plan_path, eval_stat_path)) for task_name in real_task_list]
            for result in results:
                result.get()
        except KeyboardInterrupt:
            pool.terminate()
        finally:
            pool.close()
            pool.join()

def eval_subgoal_plan_single():
    demo_dir = './igibson/data/virtual_reality'
    plan_path = './igibson/evaluation/eval_subgoal_plan/resources/log5-16-00.json'
    eval_stat_path = './igibson/log/all_checking_gpt4.json'
    # task_list = get_all_task_list()
    task_list = get_test_task_list()
    # eval_statistics = EvalStatistics(task_list, eval_stat_path)
    # real_task_list = [task_name for task_name in task_list if not eval_statistics.check_evaluated_task(task_name)]
    real_task_list = task_list
    print(len(real_task_list))
    for task_name in real_task_list:
        report = evaluate_task(task_name, demo_dir, plan_path, eval_stat_path)
        print(report)

# -----------------------------------------------
# ---------Below is the test code----------------
# -----------------------------------------------

def test_load_evolving_graph():
    demo_name = 'bottling_fruit_0_Wainscott_0_int_0_2021-05-24_19-46-46'
    demo_dir = './igibson/data/virtual_reality'
    demo_path = os.path.join(demo_dir, demo_name + '.hdf5')
    env = EvalGraphEnv(demo_path=demo_path)
    task_name = env.task.behavior_activity
    print(task_name)
    action_env = env.action_env
    print(action_env.name_to_obj)
    assert isinstance(env.task, BehaviorTask)
    print(action_env.cur_state.get_name_mapping(env.task))
    # print(action_env.cur_state.get_name_mapping())



def test_json_correctness(record_path):
    if not os.path.exists(record_path):
        with open(record_path, 'w') as f:
            json.dump({}, f)
    with open(record_path, 'r') as f:
        logs = json.load(f)
    
    demo_dir = './igibson/data/virtual_reality'
    plan_path = './igibson/evaluation/eval_subgoal_plan/resources/log5-19-17-gpt35-json-new.json'
    task_list = get_all_task_list()
    cur_num = 0
    load_success_num = 0
    for task_name in task_list:
        demo_path = os.path.join(demo_dir, task_name + '.hdf5')
        cur_num += 1
        if task_name in logs:
            task_success = logs[task_name]['success']
            if task_success:
                load_success_num += 1
            continue
        result = True
        try:
            eval_subgoal_plan = EvalSubgoalPlan(demo_path, plan_path, True)
            load_success_num += 1
            error_info = ""
        except Exception as e:
            result = False
            error_info = str(e)
            print(e)
        finally:
            temp = {
                "success": result,
                "error_info": error_info,
            }
            logs[task_name] = temp
            with open(record_path, 'w') as f:
                json.dump(logs, f, indent=4)
        print("========================")
        print("Current statistics:")
        print(f'Cur Total number of tasks: {cur_num}, Number of successfully loaded tasks: {load_success_num}')
        print("========================")


if __name__ == '__main__':
    # test_load_subgoal_plan()
    # Redirect stdout to a file
    # record_path = './igibson/log/json_new.json'
    # sys.stdout = open('./igibson/log/see_json_new.log', 'a+')
    # try:
    #     test_json_correctness(record_path=record_path)
    # finally:
    #     sys.stdout.close()
    eval_subgoal_plan()
    # eval_subgoal_plan_single()
