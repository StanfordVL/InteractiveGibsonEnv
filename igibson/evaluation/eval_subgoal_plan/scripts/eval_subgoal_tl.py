import os
import json
import igibson
import argparse
import multiprocessing

from igibson.evolving_graph.eval_evolving_graph_env import EvalGraphEnv
from igibson.tasks.behavior_task import BehaviorTask
from typing import List, Dict, Any, Optional, Tuple, Union
from igibson.evaluation.eval_subgoal_plan.subgoal_plan import SubgoalPlan, SubgoalPlanJSON, SubgoalPlanPlain, SubgoalPlanHalfJson
from igibson.evaluation.eval_subgoal_plan.checkers import Vocab, SyntacticChecker, SemanticChecker, RuntimeChecker
from igibson.evaluation.eval_subgoal_plan.state_action_translator import StateActionTranslator
from igibson.evaluation.eval_subgoal_plan.tl_formula.bddl_to_tl import translate_addressable_obj_into_tl_obj, translate_tl_obj_into_addressable_obj

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
                'info': None,
                'goal_info': None
            }
        return eval_dict
    
    def update_eval_rst_dict(self, task_name:str, success:bool, error_info:Union[str, None], goal_info: Union[Dict[str, Any], None]=None):
        self.eval_rst_dict[task_name]['success'] = success
        self.eval_rst_dict[task_name]['info'] = error_info
        self.eval_rst_dict[task_name]['goal_info'] = goal_info
    
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
        # self.subgoal_plan = SubgoalPlanPlain(plan_path, self.task_name) if not json_format else SubgoalPlanJSON(plan_path, self.task_name)
        try:
            self.subgoal_plan = SubgoalPlanHalfJson(plan_path, self.task_name)
        except Exception as e:
            raise e
    
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
            error_type = syntactic_report['error_type']
            error_category = ''
            if error_type == 'NotParseable':
                error_category = 'NotParseable'
            elif error_type == 'UnknownPrimitive':
                error_category = 'Hallucination'
            else:
                assert False, 'Unknown error type'
            error_tuple = (error_category, syntactic_report, None)
            return error_tuple
        tl_expression = syntactic_checker.get_parsed_tl_expression()
        semantic_checker = SemanticChecker(self.subgoal_plan, vocab, tl_expression, True)
        semantic_rst = semantic_checker.run_result
        if not semantic_rst:
            semantic_report = semantic_checker.report()
            error_tuple = ('Hallucination', semantic_report, None)
            return error_tuple
        runtime_checker = RuntimeChecker(self.env, self.subgoal_plan, vocab, tl_expression, True)
        runtime_report = runtime_checker.report()
        runtime_rst = runtime_checker.run_result
        if not runtime_rst:
            error_category = 'Runtime' if not runtime_checker.executable else 'GoalUnreachable'
            error_tuple = (error_category, runtime_checker.executable, runtime_report, runtime_checker.goal_info)
            return error_tuple
        return ('Correct', runtime_checker.executable, runtime_checker.feasible_action_seqs, runtime_report, runtime_checker.goal_info)
        


def get_all_task_list():
    path = os.path.join(igibson.demo_name_path)
    with open(path, 'r') as f:
        task_list = json.load(f)
    return task_list

def get_test_task_list():
    t1 = 'washing_dishes_0_Benevolence_1_int_0_2021-06-08_18-07-48'
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
    try:
        eval_subgoal_plan = EvalSubgoalPlan(demo_path, plan_path)
        report = eval_subgoal_plan.evaluate_subgoal_plan()
    except Exception as e:
        report = ('NotParseable', str(e), None)
    # eval_subgoal_plan.test_eval_graph_env()
    if test_mode == True:
        return report
    with lock:
        counter.value += 1
        print(f'Current task number: {counter.value}')
        goal_info = report[-1]
        eval_statistics = EvalStatistics(get_all_task_list(), eval_stat_path)
        if report[0] != 'Correct':
            eval_statistics.update_eval_rst_dict(task_name, False, str(report[:-1]), goal_info)
        else:
            eval_statistics.update_eval_rst_dict(task_name, True, str(report[:-1]), goal_info)
        eval_statistics.save_eval_rst_dict()
    return report

def get_one_raw_task_goal(demo_dir, task_name, error_list_dict, error_path):
    demo_path = os.path.join(demo_dir, task_name + '.hdf5')
    env = EvalGraphEnv(demo_path=demo_path)
    success_dict = env.action_env.cur_state.check_success(env.task)
    with lock:
        counter.value += 1
        error_list_dict[task_name] = success_dict
        with open(error_path, 'w') as f:
            json.dump(error_list_dict, f, indent=4)
    
def get_all_raw_task_goal():
    demo_dir = './igibson/data/virtual_reality'
    error_list_dict_path = './igibson/evaluation/eval_subgoal_plan/resources/error_list_dict.json'
    if os.path.exists(error_list_dict_path):
        with open(error_list_dict_path, 'r') as f:
            error_list_dict = json.load(f)
    else:
        error_list_dict = {}
    task_list = get_all_task_list()
    real_task_list = [task_name for task_name in task_list if not task_name in error_list_dict.keys()]
    print(f'remaining task number: {len(real_task_list)}')
    # real_task_list = real_task_list[:10] if len(real_task_list) > 10 else real_task_list

    for task_name in real_task_list:
        get_one_raw_task_goal(demo_dir, task_name, error_list_dict, error_list_dict_path)




def eval_subgoal_plan(plan_path, eval_stat_path, n_proc, task_num):
    demo_dir = './igibson/data/virtual_reality'
    task_list = get_all_task_list()
    # task_list = get_test_task_list()
    eval_statistics = EvalStatistics(task_list, eval_stat_path)
    real_task_list = [task_name for task_name in task_list if not eval_statistics.check_evaluated_task(task_name)]
    real_task_list = real_task_list[:task_num] if len(real_task_list) > task_num else real_task_list
    print(len(real_task_list))

    n_proc = min(len(real_task_list), n_proc)
    
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

def eval_subgoal_plan_single(plan_path, eval_stat_path):
    demo_dir = './igibson/data/virtual_reality'
    task_list = get_test_task_list()
    real_task_list = task_list
    print(len(real_task_list))
    for task_name in real_task_list:
        report = evaluate_task(task_name, demo_dir, plan_path, eval_stat_path)
        print(report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate subgoal plan')
    parser.add_argument('--llm_name', type=str,  default='gpt-4-turbo-2024-04-09_outputs', help='Name of the LLM')
    parser.add_argument('--n_proc', type=int, default=5, help='Number of processes')
    parser.add_argument('--max_tasks', type=int, default=100, help='Number of tasks to generate')
    parser.add_argument('--output_plan_path', type=str, default='./igibson/evaluation/eval_subgoal_plan/single_module/llm_outputs', help='Path to the LLM output plans')
    parser.add_argument('--eval_stat_path', type=str, default='./igibson/evaluation/eval_subgoal_plan/single_module/eval_stats', help='Path to store the evaluation statistics')
    args = parser.parse_args()

    llm_name = args.llm_name
    n_proc = min(multiprocessing.cpu_count(), args.n_proc)
    task_num = args.max_tasks
    base_plan_path = args.output_plan_path
    plan_path = os.path.join(base_plan_path, llm_name + '.json')
    base_stat_path = args.eval_stat_path

    # validate arguments validity in parser
    assert n_proc > 0, 'Number of processes must be greater than 0.'
    assert os.path.exists(plan_path), f'Plan path {plan_path} does not exist.'
    assert os.path.exists(base_stat_path), f'Stat path {base_stat_path} does not exist.'


    base_state_name = 'eval_'
    stat_name = llm_name.replace('_outputs', '')
    eval_stat_path = os.path.join(base_stat_path, base_state_name + stat_name + '.json')

    print(f'LLM name: {llm_name}')
    print(f'Number of processes: {n_proc}')
    print(f'Plan path: {plan_path}')
    print(f'Stat path: {eval_stat_path}')

    # get_all_raw_task_goal()

    eval_subgoal_plan(plan_path, eval_stat_path, n_proc, task_num)
    # eval_subgoal_plan_single(plan_path, eval_stat_path)


