import os
import json
from typing import Dict, Any, List, Union, Tuple

class SimpleVocab:
    def __init__(self, vocab_path='./igibson/evaluation/eval_subgoal_plan/resources/base_vocabulary.json'):
        self.vocab_path = vocab_path
        self.vocab = self.load_vocab()
        self.predicate_list = self.get_predicate_list(self.vocab)
        self.state_param_dict = self.get_state_param_dict(self.vocab)
        self.quantifiers = ['forpairs', 'forn', 'exists', 'forall', 'fornpairs']
    
    def load_vocab(self):
        with open(self.vocab_path, 'r') as f:
            vocab = json.load(f)
        return vocab
    
    def get_predicate_list(self, vocab):
        states = self.get_states(vocab)
        return states
    
    def get_state_param_dict(self, vocab):
        return vocab['state_param']
    
    @staticmethod
    def get_states(vocab: Dict[str, Any]) -> List[str]:
        return vocab['states']

class GoalAnalyzer:
    def __init__(self, task_name:str, vocab:SimpleVocab, goal_info: Dict[str, Any]) -> None:
        self.task_name = task_name
        self.vocab = vocab
        self.goal_success = goal_info['success']
        self.subgoal_list = goal_info['subgoals']
        self.subgoal_states = goal_info['subgoal_success']
        self.special_states = {'toggled_on': 'toggledon'}
        pass
    
    def check_in_quantifiers(self, subgoal):
        for part in subgoal:
            if part.lower() in self.vocab.quantifiers:
                return True
        return False
    

    def check_goal_stats(self):
        tot_node_num_fail = 0
        tot_edge_num_fail = 0
        tot_node_num_success = 0
        tot_edge_num_success = 0
        for i, subgoal in enumerate(self.subgoal_list):
            # is_quantifier = self.check_in_quantifiers(subgoal)
            node_num = 0
            edge_num = 0
            is_node_goal = False
            is_edge_goal = False
            for part in subgoal:
                if part in self.special_states:
                    part = self.special_states[part]
                if part in self.vocab.state_param_dict:
                    param_num = self.vocab.state_param_dict[part]
                    if param_num == 1:
                        is_node_goal = True
                    elif param_num == 2:
                        is_edge_goal = True
            if is_node_goal and is_edge_goal:
                node_num += 0.5
                edge_num += 0.5
            elif is_edge_goal:
                edge_num += 1
            elif is_node_goal:
                node_num += 1
            if self.subgoal_states[i]:
                tot_node_num_success += node_num
                tot_edge_num_success += edge_num
            else:
                tot_node_num_fail += node_num
                tot_edge_num_fail += edge_num
                
        return tot_node_num_fail, tot_edge_num_fail, tot_node_num_success, tot_edge_num_success
    

def analyze_llm_outputs(llm_result_path:str, error_list:Dict[str, Any]):
    with open(llm_result_path, 'r') as f:
        llm_results = json.load(f)
    
    all_goal_statisfied_num = 0
    tot_num = 0
    tot_node_goals = 0
    tot_edge_goals = 0
    satified_goals = 0
    satisfied_nodes = 0
    satisfied_edges = 0
    vocab = SimpleVocab()
    for task_name, stat_info in llm_results.items():
        try:
            goal_info = stat_info['goal_info']
            if goal_info is not None :
                goal_analyzer = GoalAnalyzer(task_name, vocab, goal_info)
                node_num_fail, edge_num_fail, node_num_success, edge_num_success = goal_analyzer.check_goal_stats()
                tot_node_goals += node_num_fail + node_num_success
                tot_edge_goals += edge_num_fail + edge_num_success
                satified_goals += node_num_success + edge_num_success
                satisfied_nodes += node_num_success
                satisfied_edges += edge_num_success
            elif goal_info is None and task_name in error_list:
                goal_info = error_list[task_name]
                goal_analyzer = GoalAnalyzer(task_name, vocab, goal_info)
                node_num_fail, edge_num_fail, node_num_success, edge_num_success = goal_analyzer.check_goal_stats()
                tot_node_goals += node_num_fail + node_num_success
                tot_edge_goals += edge_num_fail + edge_num_success
                satified_goals += node_num_success + edge_num_success
                satisfied_nodes += node_num_success
                satisfied_edges += edge_num_success
            else:
                continue
            if goal_analyzer.goal_success:
                all_goal_statisfied_num += 1
        except Exception as e:
            print('Error in task:', task_name)
            print(e)
            continue
    tot_num = tot_node_goals + tot_edge_goals
    print('All Goal Satisfied:', all_goal_statisfied_num)
    print('Total Goals:', tot_num)
    print('Total Node Goals:', tot_node_goals)
    print('Total Edge Goals:', tot_edge_goals)
    print('Satisfied Goals:', satified_goals)
    print('Satisfied Nodes:', satisfied_nodes)
    print('Satisfied Edges:', satisfied_edges)
    node_goal_success_rate = (satisfied_nodes / tot_node_goals) * 100
    edge_goal_success_rate = (satisfied_edges / tot_edge_goals) * 100
    overall_goal_success_rate = ((satified_goals) / tot_num) * 100

    print(f'Node Goal Success Rate: {node_goal_success_rate:.2f}%')
    print(f'Edge Goal Success Rate: {edge_goal_success_rate:.2f}%')
    print(f'Overall Goal Success Rate: {overall_goal_success_rate:.2f}%')

def get_eval_list():
    eval_path = './igibson/evaluation/eval_subgoal_plan/goal_inter_and_subgoal/eval_stats' # goal interpret + subgoal decomposition
    path_list = []
    for parent, dirnames, filenames in os.walk(eval_path):
        for filename in filenames:
            path_list.append(os.path.join(parent, filename))
    return path_list
if __name__ == '__main__':

    path_list = get_eval_list()
    error_list_path = './igibson/evaluation/eval_subgoal_plan/error_list_dict.json'
    with open(error_list_path, 'r') as f:
        error_list_full = json.load(f)
    error_list = error_list_full
    for llm_result_path in path_list:
        print()
        print(f'=={llm_result_path.split("/")[-1]}==')
        print()
        analyze_llm_outputs(llm_result_path, error_list)