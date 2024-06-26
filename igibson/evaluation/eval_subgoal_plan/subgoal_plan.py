import json
import random
import re
from typing import List, Dict, Any, Optional, Tuple, Union

class SubgoalPlan:
    def __init__(self, plan_path: str, task_name: str) -> None:
        self.plan_path = plan_path
        self.task_name = task_name
        
    def __str__(self) -> str:
        '''This method indicates the subgoal plan in temporal logic formula.'''
        raise NotImplementedError('This method should be implemented in the subclass.')

    def get_subgoal_plan(self) -> List[Union[str, Dict[str, Any]]]:
        '''This method indicates preprocessed subgoal plan.
        
        Args:
            None
        
        Returns:
            List[Optional[str, Dict[str, Any]]]: preprocessed subgoal plan
        '''
        raise NotImplementedError('This method should be implemented in the subclass.')
    
    def get_subgoal_plan_tl_formula(self) -> str:
        '''This method indicates the subgoal plan in temporal logic formula.
        
        Args:
            None
        
        Returns:
            str: subgoal plan in temporal logic formula
        '''
        raise NotImplementedError('This method should be implemented in the subclass.')

class SubgoalPlanJSON(SubgoalPlan):
    def __init__(self, plan_path: str, task_name: str) -> None:
        super().__init__(plan_path, task_name)
        self.subgoal_plan = self.get_subgoal_plan()
        self.subgoal_plan_tl_formula = self.get_subgoal_plan_tl_formula()

    def __str__(self) -> str:
        return self.subgoal_plan_tl_formula

    @staticmethod
    def get_predicate_form(plan_dict:Dict[str, Any]) -> str:
        operator_name = plan_dict['operator']
        params = plan_dict['params']
        new_params = []
        if operator_name != 'and' and operator_name != 'or' and operator_name != 'not':
            return f'{operator_name}({", ".join(params)})'
        elif 'for' in operator_name or 'exists' in operator_name:
            error_info = f'In get_predicate_form, failed to load the plan string:\n{plan_dict}\nError Info: Quantifiers are not supported yet.'
            raise NotImplementedError('Quantifiers are not supported yet.')
        for p in params:
            if isinstance(p, dict):
                p = SubgoalPlanJSON.get_predicate_form(p)
            new_params.append(p)
        if operator_name == 'not':
            return f'not ({new_params[0]})'
        else:
            return f" {operator_name} ".join(new_params)


    def get_subgoal_plan(self) -> List[Dict[str, Any]]:
        try:
            with open(self.plan_path, 'r') as f:
                plans = json.load(f)
            raw_plan_str = plans[self.task_name]['output']
            plan_dicts = SubgoalPlanJSON.load_plan_str(raw_plan_str)
            assert isinstance(plan_dicts, list), f'Invalid plan format: {plan_dicts}'
            new_plans = [SubgoalPlanJSON.sample_concrete_plan(plan) for plan in plan_dicts]
        except Exception as e:
            error_info = f'In get_subgoal_plan, failed to load the subgoal plan for task {self.task_name}\nError Info: {e}'
            raise Exception(error_info)
        return new_plans
    
    @staticmethod
    def load_plan_str(plan_str: str) -> List[Dict[str, Any]]:
        plan_str = plan_str.strip('[').strip(']').strip()
        plan_dicts = plan_str.split('\n')
        new_plans = []
        for plan_dict in plan_dicts:
            plan_dict = plan_dict.strip().strip(',')
            if plan_dict == '':
                continue
            try:
                new_plans.append(json.loads(plan_dict))
            except Exception as e:
                error_info = f'In load_plan_str, failed to load the plan string:\n{plan_dict}\nError Info: {e}'
                raise Exception(error_info)
        return new_plans

    @staticmethod
    def sample_concrete_plan(plan_dict: Dict[str, Any]) -> Dict[str, Any]:
        new_plan_dict = {}
        assert 'operator' in plan_dict and 'params' in plan_dict, f'Invalid plan format: {plan_dict}'
        new_plan_dict['operator'] = plan_dict['operator']
        new_plan_dict['params'] = []
        if plan_dict['operator'] != 'and' and plan_dict['operator'] != 'or' and plan_dict['operator'] != 'not':
            return plan_dict
        elif 'for' in plan_dict['operator'] or 'exists' in plan_dict['operator']:
            error_info = f'In sample_concrete_plan, failed to load the plan string:\n{plan_dict}\nError Info: Quantifiers are not supported yet.'
            raise NotImplementedError(error_info)
        for p in plan_dict['params']:
            if isinstance(p, dict) and plan_dict['operator'] != 'or':
                p = SubgoalPlanJSON.sample_concrete_plan(p)
            elif isinstance(p, dict) and plan_dict['operator'] == 'or':
                if random.random() < 0.5:
                    p = SubgoalPlanJSON.sample_concrete_plan(p)
                    return p
            new_plan_dict['params'].append(p)
        return new_plan_dict

    def get_subgoal_plan_tl_formula(self) -> str:
        plan_str_list = [SubgoalPlanJSON.get_predicate_form(plan) for plan in self.subgoal_plan]
        return ' then '.join(plan_str_list)
    

class SubgoalPlanPlain(SubgoalPlan):
    def __init__(self, plan_path: str, task_name: str) -> None:
        super().__init__(plan_path, task_name)
        self.subgoal_plan = self.get_subgoal_plan()
        self.subgoal_plan_tl_formula = self.get_subgoal_plan_tl_formula()
        self.simple_subgoal_plan = self.get_simple_subgoal_plan()
    
    def __str__(self) -> str:
        return '\n'.join(self.subgoal_plan)
    
    def tl_formula_str(self) -> str:
        return self.subgoal_plan_tl_formula
    
    def get_subgoal_plan(self) -> List[str]:
        with open(self.plan_path, 'r') as f:
            plans = json.load(f)
        raw_plan_str = plans[self.task_name]['output']
        subgoal_plan_list = self.preprocess_raw_plan_str(raw_plan_str)
        return subgoal_plan_list
    
    @staticmethod
    def preprocess_raw_plan_str(raw_plan_str: str) -> List[str]:
        raw_plan_list = raw_plan_str.strip().split('\n')
        subgoal_plan_list = []
        for state in raw_plan_list:
            state = state.strip()
            if state != '' and 'agent' not in state:
                sampled_state = SubgoalPlanPlain.sample_state_from_compound_state(state)
                subgoal_plan_list.append(sampled_state)
        return subgoal_plan_list
    
    @staticmethod
    def sample_state_from_compound_state(compound_state: str) -> str:
        quantifiers = ['forall', 'exists', 'forpairs', 'forn', 'fornpairs']
        if any(quantifier in compound_state for quantifier in quantifiers):
            raise NotImplementedError('Quantifiers are not supported yet.')
        states_or = compound_state.split(' or ')
        sampled_state = random.choice(states_or)
        # to do: support all possible orders of states_and
        # currently, we maintain the order of states_and
        return sampled_state
    
    def get_subgoal_plan_tl_formula(self) -> str:
        return ' then '.join(self.subgoal_plan)
    
    def get_simple_subgoal_plan(self) -> List[str]:
        simple_subgoal_plan = []
        for state in self.subgoal_plan:
            states_and = state.split(' and ')
            simple_subgoal_plan.extend(states_and)
        return simple_subgoal_plan
    

class SubgoalPlanHalfJson(SubgoalPlan):
    def __init__(self, plan_path: str, task_name: str) -> None:
        super().__init__(plan_path, task_name)
        self.subgoal_plan = self.get_subgoal_plan()
        self.subgoal_plan_tl_formula = self.get_subgoal_plan_tl_formula()
        self.simple_subgoal_plan = self.get_simple_subgoal_plan()
    
    def __str__(self) -> str:
        return '\n'.join(self.subgoal_plan)
    
    def tl_formula_str(self) -> str:
        return self.subgoal_plan_tl_formula
    
    @staticmethod
    def extract_json_obj(plan_str: str)-> Union[Dict[str, Any], None]:
        raw_plan_str = plan_str.strip().replace('}}', '}')
        raw_plan_str = raw_plan_str.replace('toggled.on', 'toggledon').replace('t-shirt', 'shirt')
        match = re.search(r"{[^{}]*}", raw_plan_str, re.DOTALL)
        if match:
            result = match.group(0)
            try:
                json_obj = json.loads(result)
                assert 'output' in json_obj, 'output key is not in json_obj'
                assert isinstance(json_obj['output'], list), 'output value is not list'
            except Exception as e:
                return None
            return json_obj
        return None
    
    def get_llm_output(self, plans) -> str:
        for plan in plans:
            if self.task_name in plan['identifier']:
                return plan['llm_output']
        return ''

    def get_subgoal_plan(self) -> List[str]:
        with open(self.plan_path, 'r') as f:
            plans = json.load(f)
        raw_plan_str = self.get_llm_output(plans)
        assert raw_plan_str != '', f'Failed to get the plan string for task {self.task_name}'
        json_obj = SubgoalPlanHalfJson.extract_json_obj(raw_plan_str)
        if json_obj is None:
            raise Exception(f'Failed to extract json object from the plan string: {raw_plan_str}')
        subgoal_plan_list = self.preprocess_raw_plan_obj(json_obj)
        return subgoal_plan_list
    
    @staticmethod
    def preprocess_raw_plan_obj(plan_obj: Dict[str, List[str]]) -> List[str]:
        raw_plan_list = plan_obj['output']
        subgoal_plan_list = []
        for state in raw_plan_list:
            state = state.strip()
            if state != '' and 'agent' not in state:
                sampled_state = SubgoalPlanHalfJson.sample_state_from_compound_state(state)
                subgoal_plan_list.append(sampled_state) if sampled_state != '' else None
        return subgoal_plan_list
    
    @staticmethod
    def sample_state_from_compound_state(compound_state: str) -> str:
        quantifiers = ['forall', 'exists', 'forpairs', 'forn', 'fornpairs']
        if any(quantifier in compound_state for quantifier in quantifiers):
            # raise NotImplementedError('Quantifiers are not supported yet.')
            print(f'Quantifiers are not supported yet: {compound_state}')
            return ''
        states_or = compound_state.split(' or ')
        sampled_state = random.choice(states_or)
        # to do: support all possible orders of states_and
        # currently, we maintain the order of states_and
        return sampled_state
    
    def get_subgoal_plan_tl_formula(self) -> str:
        return ' then '.join(self.subgoal_plan)
    
    def get_simple_subgoal_plan(self) -> List[str]:
        simple_subgoal_plan = []
        for state in self.subgoal_plan:
            states_and = state.split(' and ')
            simple_subgoal_plan.extend(states_and)
        return simple_subgoal_plan
