import copy
import json
import os
import sys

from igibson.evaluation.eval_subgoal_plan.subgoal_plan import SubgoalPlanJSON, SubgoalPlanPlain, SubgoalPlan
from collections import deque
from igibson.evaluation.eval_subgoal_plan.state_action_translator import StateActionTranslator
from igibson.evolving_graph.eval_evolving_graph_env import EvalGraphEnv
from igibson.evolving_graph.evolving_graph import EvolvingGraph, GraphState, ErrorType, ErrorInfo
from igibson.evaluation.eval_subgoal_plan.tl_formula.simple_tl_parser import parse_simple_tl
from igibson.evaluation.eval_subgoal_plan.tl_formula.simple_tl import SimpleTLExpression, Proposition, Action
from igibson.evaluation.eval_subgoal_plan.tl_formula.simple_tl import extract_args, extract_propositions_and_actions, sample_a_determined_path_from_tl_expr
from typing import List, Dict, Any, Optional, Tuple, Union

class Vocab:
    def __init__(self, name_mapping: List[Dict[str, str]], relevant_objects: List[str], vocab_path: str='./igibson/evaluation/eval_subgoal_plan/resources/base_vocabulary.json'):
        self.vocab_path = vocab_path
        self.vocab = self.load_vocab()
        self.name_mapping = name_mapping
        self.predicate_list = self.get_predicates()
        self.action_list = self.get_actions(self.vocab)
        self.relevant_objects = relevant_objects
        self.action_param_dict = self.get_action_param_dict(self.vocab)
        self.state_param_dict = self.get_state_param_dict(self.vocab)
        self.alias_dict = {
            "toggleon": "toggled_on",
            "toggledon": "toggled_on",
            "toggled_on": "toggledon"
        }

    def load_vocab(self):
        with open(self.vocab_path, 'r') as f:
            vocab = json.load(f)
        return vocab
    
    def get_predicates(self) -> List[str]:
        states = self.get_states(self.vocab)
        properties = self.get_properties(self.name_mapping)
        return states + properties

    @staticmethod
    def get_states(vocab: Dict[str, Any]) -> List[str]:
        return vocab['states']
    
    @staticmethod
    def get_actions(vocab: Dict[str, Any]) -> List[str]:
        return vocab['actions']
    
    @staticmethod
    def get_properties(name_mapping: List[Dict[str, str]]) -> List[str]:
        set_properties = set(item['category'] for item in name_mapping)
        return list(set_properties)
    
    @staticmethod
    def get_action_param_dict(vocab: Dict[str, Any]) -> Dict[str, int]:
        return vocab['action_param']
    
    @staticmethod
    def get_state_param_dict(vocab: Dict[str, Any]) -> Dict[str, int]:
        return vocab['state_param']
    
    def safe_compare_two_states(self, state_1:str, state_2:str) -> bool:
        state_1 = self.alias_dict[state_1] if state_1 in self.alias_dict else state_1
        state_2 = self.alias_dict[state_2] if state_2 in self.alias_dict else state_2
        state_1 = state_1.lower().strip()
        state_2 = state_2.lower().strip()

        # todo: hold hands need more attention to take care

        return state_1 == state_2

    def safe_compare_two_actions(self, action_1:str, action_2:str) -> bool:
        action_1 = self.alias_dict[action_1] if action_1 in self.alias_dict else action_1
        action_2 = self.alias_dict[action_2] if action_2 in self.alias_dict else action_2
        action_1 = action_1.lower().strip()
        action_2 = action_2.lower().strip()
        return action_1 == action_2
        ...
    
    def check_state_in_vocab(self, state:str) -> bool:
        ''' This can only be used when calling states defined in evolving graph. Not for states generated in subgoal plans.

        Args:
            state (str): state to be checked

        Returns:
            bool: whether the state is in the vocabulary
        '''
        if state.startswith('Is') or state.startswith('In'):
            state = 'i' + state[1:]
        else:
            state = state.lower().strip()
            state = self.alias_dict[state] if state in self.alias_dict else state
        return state.strip() in self.predicate_list
    
    def check_action_in_vocab(self, state:str) -> bool:
        ''' This can only be used when calling actions defined in evolving graph. Not for actions generated in subgoal plans.
        
        Args:
            action (str): action to be checked
            
        Returns:
            bool: whether the action is in the vocabulary
        '''
        action = state.lower().strip()
        action = self.alias_dict[action] if action in self.alias_dict else action
        return action in self.action_list

class BaseChecker:
    def __init__(self, subgoal_plan: SubgoalPlan, vocab: Vocab) -> None:
        self.subgoal_plan = subgoal_plan
        self.vocab = vocab
        self.task_name = self.subgoal_plan.task_name
        self.tl_formula = self.subgoal_plan.get_subgoal_plan_tl_formula()
        ...
    
    def run_checker(self) -> bool:
        '''This method runs the checker to check the subgoal plan.
        
        Returns:
            bool: whether the subgoal plan is correct'''
        raise NotImplementedError('This method should be implemented in the subclass.')

    def update_statistics(self, error_info) -> None:
        '''This method updates the statistics based on the result.
        
        Args:
            result (Dict): checking result of the subgoal plan
        
        Returns:
            None
        '''
        raise NotImplementedError('This method should be implemented in the subclass.')
    
    def report(self) -> Dict[Any, Any]:
        '''This method reports the statistics of the subgoal plan.
        
        Args:
            None
        
        Returns:
            Dict[Any, Any]: statistics of the subgoal plan
        '''
        raise NotImplementedError('This method should be implemented in the subclass.')
    

class SyntacticChecker(BaseChecker):
    def __init__(self, subgoal_plan:SubgoalPlan, vocab:Vocab) -> None:
        super().__init__(subgoal_plan, vocab)
        self.error_type = None
        self.error_info = None
        self.run_result = self.run_checker()
    
    def update_statistics(self, error_type, error_info) -> None:
        self.error_type = error_type
        self.error_info = error_info

    

    def run_checker(self) -> bool:
        try:
            self.parsed_tl_expression = parse_simple_tl(self.tl_formula, self.vocab.predicate_list, self.vocab.action_list)
        except Exception as e:
            error_type = str(e.__class__.__name__)
            error_info = str(e)
            self.update_statistics(error_type, error_info)
            return False
        return True
    
    def get_parsed_tl_expression(self) -> SimpleTLExpression:
        assert self.run_result, f'Cannot get parsed temporal logic expression for incorrect subgoal plan'
        return self.parsed_tl_expression
    
    def report(self) -> Dict[str, Any]:
        return {
            'task_name': self.task_name,
            'syntactic_check': self.run_result,
            'error_type': self.error_type,
            'error_info': self.error_info
        }

class SemanticChecker(BaseChecker):
    def __init__(self, subgoal_plan:SubgoalPlan, vocab:Vocab, parsed_tl_expression:SimpleTLExpression, syntactic_rst:bool) -> None:
        super().__init__(subgoal_plan, vocab)
        self.tl_expression = parsed_tl_expression
        self.error_dict = {
            "task_name": self.task_name,
            "IncorrectParamLength": True,
            "ObjectNotInScene": True,
            "error_info": ""
        }
        self.run_result = self.run_checker() if syntactic_rst else False
    
    def update_statistics(self, error_type, error_info) -> None:
        assert error_type in self.error_dict, f'Unknown error type {error_type}'
        self.error_dict[error_type] = False
        self.error_dict["error_info"] += f'{error_info}\n'

    def check_param_length(self) -> bool:
        propostions, actions = extract_propositions_and_actions(self.tl_expression)
        primitives = propostions + actions
        for primitive in primitives:
            if isinstance(primitive, Proposition):
                state_name = primitive.name
                grounded_param_num = self.vocab.state_param_dict[state_name]
                cur_param_num = len(primitive.args)
            elif isinstance(primitive, Action):
                action_name = primitive.name
                grounded_param_num = self.vocab.action_param_dict[action_name]
                cur_param_num = len(primitive.args)
            else:
                raise ValueError(f'Unknown primitive type {type(primitive)}')
            if cur_param_num != grounded_param_num:
                self.update_statistics('IncorrectParamLength', f'Primitive {primitive} has incorrect number of parameters')
                return False
        return True

    def check_objects_in_scence(self) -> bool:
        generate_objects = extract_args(self.tl_expression)
        for obj in generate_objects:
            if obj not in self.vocab.relevant_objects:
                self.update_statistics('ObjectNotInScene', f'Object {obj} is not in the scene')
                return False
        return True

    def run_checker(self) -> bool:
        param_check_rst = self.check_param_length()
        obj_check_rst = self.check_objects_in_scence()
        return param_check_rst and obj_check_rst
    
    def report(self) -> Dict[str, Any]:
        return self.error_dict


class RuntimeChecker(BaseChecker):
    def __init__(self, env:EvalGraphEnv, subgoal_plan: SubgoalPlan, vocab: Vocab, tl_expression: SimpleTLExpression, semantic_rst: bool) -> None:
        super().__init__(subgoal_plan, vocab)
        self.tl_expression = tl_expression
        self.env = env
        self.det_subgoal_tl_list = sample_a_determined_path_from_tl_expr(self.tl_expression)
        self.state_action_translator = StateActionTranslator(self.det_subgoal_tl_list, env.action_env)
        self.feasible_action_seqs = []
        self.error_info = []
        self.executable = False
        self.run_result = self.run_checker() if semantic_rst else False
    
    def execute_subgoal_plan(self):
        prev_action_env_state = copy.deepcopy(self.env.action_env.cur_state)
        prev_saved_history_state = copy.deepcopy(self.env.action_env.history_states)
        prev_executed_action_list = []
        remained_subgoals = self.det_subgoal_tl_list
        prev_error_info_list = []
        level = 0

        exec_queue = deque()
        prev = (prev_action_env_state, prev_executed_action_list, remained_subgoals, prev_saved_history_state, prev_error_info_list, level)
        exec_queue.append(prev)

        feasible_action_seqs = []
        failed_action_seqs = []
        correct_plan = False
        executable = False

        while exec_queue:
            cur_action_env_state, cur_executed_action_list, cur_remained_subgoals, cur_saved_history_state, cur_error_info_list, cur_level = exec_queue.popleft()
            prev_action_env_state = copy.deepcopy(cur_action_env_state)
            prev_saved_history_state = copy.deepcopy(cur_saved_history_state)
            prev_error_info_list = copy.deepcopy(cur_error_info_list)
            if len(cur_remained_subgoals) == 0:
                executable = True
                self.executable = True
                success = self.env.action_env.cur_state.check_success(self.env.task)
                if success:
                    feasible_action_seqs.append(cur_executed_action_list)
                    correct_plan = True
                else:
                    # for future error analysis, temporaliy assigned as missing step
                    error_info = ErrorInfo()
                    error_info.update_error(ErrorType.MISSING_STEP, 'Final goal not satisfied')
                    cur_error_info_list.append([error_info.report_error(), None, None])
                    failed_action_seqs.append((cur_executed_action_list, cur_error_info_list))
            else:
                cur_subgoal = cur_remained_subgoals[0]
                next_subgoal = cur_remained_subgoals[1] if len(cur_remained_subgoals) > 1 else None
                self.env.update_evolving_graph_state(copy.deepcopy(prev_action_env_state), copy.deepcopy(prev_saved_history_state))
                is_combined_states, action_candidates = self.state_action_translator.map_subgoal_to_action_sequence_dynamic_version(cur_subgoal, next_subgoal, self.env.action_env)
                for action_set in action_candidates:
                    self.env.update_evolving_graph_state(copy.deepcopy(prev_action_env_state), copy.deepcopy(prev_saved_history_state))
                    cur_error_info_list = copy.deepcopy(prev_error_info_list)
                    # self.env.action_env = copy.deepcopy(prev_action_env)
                    success = True
                    for action in action_set:
                        action_name = action['action']
                        action_args = action['object']
                        rst, error_info = self.env.eval_subgoal_apply_action(action_name, action_args)
                        if not rst:
                            error_dict = error_info.report_error()
                            error_type = error_dict['error_type']
                            cur_error_info_list.append([error_info.report_error(), cur_subgoal, action])
                            if error_type[0] != str(ErrorType.ADDITIONAL_STEP):
                                success = False
                                failed_action_seq = copy.deepcopy(cur_executed_action_list) + action_set
                                failed_error_info_list = copy.deepcopy(cur_error_info_list)
                                failed_action_seqs.append((failed_action_seq, failed_error_info_list))
                                break
                    if success:
                        new_action_env_state = copy.deepcopy(self.env.action_env.cur_state)
                        new_executed_actions = copy.deepcopy(cur_executed_action_list)
                        new_executed_actions.extend(action_set)
                        if is_combined_states:
                            new_remained_subgoals = copy.deepcopy(cur_remained_subgoals[2:]) if len(cur_remained_subgoals) > 2 else []
                        else:
                            new_remained_subgoals = copy.deepcopy(cur_remained_subgoals[1:]) if len(cur_remained_subgoals) > 1 else []
                        new_saved_history_state = copy.deepcopy(self.env.action_env.history_states)
                        new_error_info_list = copy.deepcopy(cur_error_info_list)
                        new_level = cur_level + 1
                        new_rst = (new_action_env_state, new_executed_actions, new_remained_subgoals, new_saved_history_state, new_error_info_list, new_level)
                        exec_queue.append(new_rst)
        if len(feasible_action_seqs) > 0:
            print('==[Has a feasible plan!]==')
        return executable, correct_plan, feasible_action_seqs, failed_action_seqs
    
    def run_checker(self) -> bool:
        executable, correct_plan, feasible_action_seqs, failed_action_seqs = self.execute_subgoal_plan()
        if len(failed_action_seqs) > 0:
            for fail_info in failed_action_seqs:
                failed_action_seq = fail_info[0]
                failed_error_info_list = fail_info[1]
                for failed_error_info_dict in failed_error_info_list:
                    failed_subgoal = failed_error_info_dict[1]
                    failed_action = failed_error_info_dict[2]
                    tmp_dict = {
                        'failed_action_sequence': failed_action_seq,
                        'failed_subgoal': str(failed_subgoal),
                        'failed_action': failed_action,
                        'error_info': failed_error_info_dict[0]
                    }
                    self.update_statistics(tmp_dict)
        # for i, action_seq in enumerate(feasible_action_seqs):
        #     print(f"Feasible action sequence {i}:")
        #     for action in action_seq:
        #         print(f"  {action}")
        #     print(f"------------------")
        self.feasible_action_seqs = feasible_action_seqs
        return executable and correct_plan and len(self.feasible_action_seqs) > 0
    
    def update_statistics(self, error_info) -> None:
        self.error_info.append(error_info)
    
    def report(self) -> List[Dict[Any, Any]]:
        return self.error_info


    def test_state_action_translator(self):
        action_sequence = self.state_action_translator.map_subgoal_to_action_sequence_static_version()
        for action_candidates in action_sequence:
            for i, action in enumerate(action_candidates):
                print(f'Action set {i}')
                for act in action:
                    print(f'  {act}')
                print(f'------------')
        ...

    def print_det_subgoal_tl_list(self):
        for primitive in self.det_subgoal_tl_list:
            print(primitive)

