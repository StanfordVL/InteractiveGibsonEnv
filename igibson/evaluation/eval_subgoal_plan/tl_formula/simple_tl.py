#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# File   : simple_tl.py
# Author : Jiayuan Mao
# Email  : maojiayuan@gmail.com
# Date   : 04/11/2024
#
# Distributed under terms of the MIT license.

from dataclasses import dataclass
from typing import Optional, Union, Sequence, List, Set, Dict, Tuple


@dataclass
class Proposition(object):
    name: str
    args: List[str]

    def __str__(self):
        return '{}({})'.format(self.name, ', '.join(self.args))

def build_id_to_name_dict(objs: List[str]):
    import re
    # an object is in the form of "name.id"
    pattern = re.compile(r'(\w+)\.(\d+)')
    id_to_name = {}
    for obj in objs:
        match = pattern.search(obj)
        assert match, f'Failed to match pattern in {obj}'
        id_to_name[match.group(2)] = match.group(1)
    return id_to_name

def build_name_to_id_list_dict(objs: List[str]):
    import re
    # an object is in the form of "name.id"
    pattern = re.compile(r'(\w+)\.(\d+)')
    name_to_id_list = {}
    for obj in objs:
        match = pattern.search(obj)
        assert match, f'Failed to match pattern in {obj}'
        if match.group(1) not in name_to_id_list:
            name_to_id_list[match.group(1)] = []
        name_to_id_list[match.group(1)].append(match.group(2))
    
    # sort the list for each name
    for name, id_list in name_to_id_list.items():
        name_to_id_list[name] = sorted(id_list)
    return name_to_id_list

def get_first_object_id(name_to_id_list: Dict[str, List[str]], obj_name):
    assert obj_name in name_to_id_list, f'{obj_name} not in name_to_id_list'
    assert len(name_to_id_list[obj_name]) > 0, f'{obj_name} has no id'
    return name_to_id_list[obj_name][0]

def get_all_object_ids(name_to_id_list: Dict[str, List[str]], obj_name):
    assert obj_name in name_to_id_list, f'{obj_name} not in name_to_id_list'
    return name_to_id_list[obj_name]

def get_random_object_id(name_to_id_list: Dict[str, List[str]], obj_name):
    import random
    assert obj_name in name_to_id_list, f'{obj_name} not in name_to_id_list'
    assert len(name_to_id_list[obj_name]) > 0, f'{obj_name} has no id'
    return random.choice(name_to_id_list[obj_name])

def get_id_name(id_to_name: Dict[str, str], obj_id):
    assert obj_id in id_to_name, f'{obj_id} not in id_to_name'
    return id_to_name[obj_id]

def has_id(object:str) -> bool:
    import re
    # an object can be in the form of "name.id" or just "name"
    pattern = re.compile(r'(\w+)\.(\d+)')
    match = pattern.search(object)
    # if the object has an id, return True, if the object only has a name, return False
    return bool(match)

def full_id_objects(objects: List[str]) -> bool:
    '''
    This function assesses whether there is any object in the list of objects that does not have an id.
    ''' 
    for obj in objects:
        if not has_id(obj):
            return False
    return True

def parse_propositions(props: Union[Sequence[Proposition], Proposition], objects: List[str]):
    if not full_id_objects(objects):
        return props if not isinstance(props, Proposition) else [props]
    name_to_id_dict = build_name_to_id_list_dict(objects)
    new_props = list()
    if isinstance(props, Proposition):
        props = [props]
    for prop in props:
        prop_name = prop.name
        prop_args = prop.args
        parsed_args = []
        for arg in prop_args:
            if has_id(arg):
                parsed_args.append(arg)
            else:
                first_id = get_first_object_id(name_to_id_dict, arg)
                object_str = f'{arg}.{first_id}'
                parsed_args.append(object_str)
        new_props.append(Proposition(prop_name, parsed_args))
    return new_props


class State(object):
    def __init__(self, objects: List[str], propositions: Sequence[Proposition]):
        self.objects = objects
        new_propositions = parse_propositions(propositions, objects)
        self.propositions = {str(p): p for p in new_propositions}

    def __str__(self):
        return 'State({})'.format(', '.join(map(str, self.propositions)))

    def eval(self, proposition: Proposition):
        return str(proposition) in self.propositions


@dataclass
class Action(object):
    name: str
    args: List[str]

    def __str__(self):
        return '{}({})'.format(self.name, ', '.join(self.args))

    def equals(self, other: 'Action'):
        # this part needs further modification, but not now.
        # when I start to write runtime checking, I will get back to this part to see what can I do to make this work
        return self.name == other.name and tuple(self.args) == tuple(other.args)


class StateActionSequence(object):
    def __init__(self, states: List[State], actions: List[Action]):
        self.states = states
        self.actions = actions

        assert len(states) == len(actions) + 1 or len(states) == len(actions) == 0, 'The number of states and actions should differ by 1.'

    def iter_sa_pairs(self):
        for state, action in zip(self.states, self.actions):
            yield state, action
        if len(self.states) > 0:
            yield self.states[-1], None

    def exclude_prefix(self, prefix_length: int):
        if prefix_length >= len(self.states):
            return StateActionSequence([], [])
        return StateActionSequence(self.states[prefix_length:], self.actions[prefix_length:])

    def __str__(self):
        return 'StateActionSequence({}, {})'.format(self.states, self.actions)


@dataclass
class EvaluationResult(object):
    rv: bool
    """The result of the evaluation."""

    shortest_prefix: int
    """The length of the shortest prefix that satisfies the expression. If the expression is never satisfied, this should be -1."""


class SimpleTLExpression(object):
    """A simple temporal logic expression.

    There are two types of expressions: state goals and temporal goals.

    - State goals are evaluated on a single state-action pair. When we evaluate a state-goal expression on a trajectory,
        we return True if there exists a state-action pair in the trajectory that satisfies the expression.
    - Temporal goals are evaluated on a trajectory. It can only be evaluated on a trajectory, but not on a single state-action pair.

    :meth:`eval_state` is used to evaluate the expression on a single state-action pair.
    :meth:`eval` is used to evaluate the expression on a trajectory.

    To handle free variables (in forall and exists), we use a variable mapping to map variables to our "guessed" grounding.
    """

    def __init__(self, is_state_goal: bool):
        self.is_state_goal = is_state_goal
        self.is_temporal_goal = not is_state_goal

    def eval_state(self, state: State, action: Optional[Action], variable_mapping: Dict[str, str]) -> bool:
        """Evaluate the expression on the given state-action pair.

        Args:
            state: the state to evaluate the expression on.
            action: the action to evaluate the expression on.
            variable_mapping: a mapping from variables to their values.

        Returns:
            bool: the return value of the expression.
        """
        raise NotImplementedError('eval_state is not implemented.')

    def eval(self, trajectory: StateActionSequence, variable_mapping: Dict[str, str]) -> EvaluationResult:
        """Evaluate the expression on the given trajectory.

        Args:
            trajectory: the trajectory to evaluate the expression on.
            variable_mapping: a mapping from variables to their values.

        Returns:
            EvaluationResult: the evaluation result, including the boolean value and the shortest prefix length.
        """
        raise NotImplementedError('eval is not implemented.')


class SimpleTLPrimitive(SimpleTLExpression):
    def __init__(self, prop_or_action: Union[Proposition, Action]):
        # NB(Jiayuan Mao @ 2024/04/11): Primitive expressions are always state-goal expressions.
        super().__init__(is_state_goal=True)
        self.prop_or_action = prop_or_action
        self.is_proposition = isinstance(prop_or_action, Proposition)
        self.is_action = isinstance(prop_or_action, Action)

    def __str__(self):
        return str(self.prop_or_action)

    def ground(self, variable_mapping: Dict[str, str]):
        if self.is_proposition:
            return SimpleTLPrimitive(Proposition(self.prop_or_action.name, [variable_mapping.get(arg, arg) for arg in self.prop_or_action.args]))
        elif self.is_action:
            return SimpleTLPrimitive(Action(self.prop_or_action.name, [variable_mapping.get(arg, arg) for arg in self.prop_or_action.args]))

    def eval_state(self, state: State, action: Optional[Action], variable_mapping: Dict[str, str]) -> bool:
        ground_self = self.ground(variable_mapping)
        if self.is_proposition:
            return state.eval(ground_self.prop_or_action)
        elif self.is_action:
            if action is None:
                return False
            return action.equals(ground_self.prop_or_action)
        else:
            raise ValueError('Unknown prop_or_action type.')

    def eval(self, trajectory: StateActionSequence, variable_mapping: Dict[str, str]) -> EvaluationResult:
        for i, (s, a) in enumerate(trajectory.iter_sa_pairs()):
            if self.eval_state(s, a, variable_mapping):
                return EvaluationResult(rv=True, shortest_prefix=i + 1)
        return EvaluationResult(rv=False, shortest_prefix=-1)


class SimpleTLAnd(SimpleTLExpression):
    def __init__(self, *args: SimpleTLExpression):
        is_state_goal = None
        for arg in args:
            if is_state_goal is None:
                is_state_goal = arg.is_state_goal
            else:
                assert is_state_goal == arg.is_state_goal, 'Mixed state and temporal goals are not allowed in a conjunction.'
        super().__init__(is_state_goal=is_state_goal)
        self.args = args

    def __str__(self):
        return 'And({})'.format(', '.join(map(str, self.args)))

    def eval_state(self, state: State, action: Optional[Action], variable_mapping: Dict[str, str]) -> bool:
        return all(arg.eval_state(state, action, variable_mapping) for arg in self.args)

    def eval(self, trajectory: StateActionSequence, variable_mapping: Dict[str, str]) -> EvaluationResult:
        if self.is_state_goal:
            for i, (s, a) in enumerate(trajectory.iter_sa_pairs()):
                if self.eval_state(s, a, variable_mapping):
                    return EvaluationResult(rv=True, shortest_prefix=i + 1)
            return EvaluationResult(rv=False, shortest_prefix=-1)
        else:
            global_index = -1
            for arg in self.args:
                result = arg.eval(trajectory, variable_mapping)
                if not result.rv:
                    return EvaluationResult(rv=False, shortest_prefix=-1)
                global_index = max(global_index, result.shortest_prefix)
            return EvaluationResult(rv=True, shortest_prefix=global_index)


class SimpleTLOr(SimpleTLExpression):
    def __init__(self, *args: SimpleTLExpression):
        is_state_goal = None
        for arg in args:
            if is_state_goal is None:
                is_state_goal = arg.is_state_goal
            else:
                # assert is_state_goal == arg.is_state_goal, 'Mixed state and temporal goals are not allowed in a conjunction.'
                is_state_goal &= arg.is_state_goal # Changed to allow mixed state and temporal goals and set is_state_goal to False if any of the args is temporal goal
        super().__init__(is_state_goal=is_state_goal)
        self.args = args

    def __str__(self):
        return 'Or({})'.format(', '.join(map(str, self.args)))

    def eval_state(self, state: State, action: Optional[Action], variable_mapping: Dict[str, str]) -> bool:
        return any(arg.eval_state(state, action, variable_mapping) for arg in self.args)

    def eval(self, trajectory: StateActionSequence, variable_mapping: Dict[str, str]) -> EvaluationResult:
        if self.is_state_goal:
            for i, (s, a) in enumerate(trajectory.iter_sa_pairs()):
                if self.eval_state(s, a, variable_mapping):
                    return EvaluationResult(rv=True, shortest_prefix=i + 1)
            return EvaluationResult(rv=False, shortest_prefix=-1)
        else:
            global_index = 1e9
            for arg in self.args:
                result = arg.eval(trajectory, variable_mapping)
                if result.rv:
                    global_index = min(global_index, result.shortest_prefix)
            return EvaluationResult(rv=global_index < 1e9, shortest_prefix=global_index)


class SimpleTLNot(SimpleTLExpression):
    def __init__(self, arg: SimpleTLExpression):
        super().__init__(is_state_goal=arg.is_state_goal)
        self.arg = arg

    def __str__(self):
        return 'Not({})'.format(self.arg)

    def eval_state(self, state: State, action: Optional[Action], variable_mapping: Dict[str, str]) -> bool:
        return not self.arg.eval_state(state, action, variable_mapping)

    def eval(self, trajectory: StateActionSequence, variable_mapping: Dict[str, str]) -> EvaluationResult:
        if self.is_state_goal:
            for i, (s, a) in enumerate(trajectory.iter_sa_pairs()):
                if self.eval_state(s, a, variable_mapping):
                    return EvaluationResult(rv=True, shortest_prefix=i + 1)
            return EvaluationResult(rv=False, shortest_prefix=-1)
        else:
            result = self.arg.eval(trajectory, variable_mapping)
            # For negated temporal goals, the shortest prefix is the length of the trajectory if the goal is never satisfied.
            return EvaluationResult(rv=not result.rv, shortest_prefix=len(trajectory.states) if result.rv else -1)


class SimpleTLImplies(SimpleTLExpression):
    def __init__(self, left: SimpleTLExpression, right: SimpleTLExpression):
        assert left.is_state_goal and right.is_state_goal, 'Implication is only allowed between state goals.'
        super().__init__(is_state_goal=True)
        self.left = left
        self.right = right

    def __str__(self):
        return 'Implies({}, {})'.format(self.left, self.right)

    def eval_state(self, state: State, action: Optional[Action], variable_mapping: Dict[str, str]) -> bool:
        return not self.left.eval_state(state, action, variable_mapping) or self.right.eval_state(state, action, variable_mapping)

    def eval(self, trajectory: StateActionSequence, variable_mapping: Dict[str, str]) -> EvaluationResult:
        if self.is_state_goal:
            for i, (s, a) in enumerate(trajectory.iter_sa_pairs()):
                if self.eval_state(s, a, variable_mapping):
                    return EvaluationResult(rv=True, shortest_prefix=i + 1)
            return EvaluationResult(rv=False, shortest_prefix=-1)
        else:
            raise ValueError('Temporal implication is not supported.')


class SimpleTLForall(SimpleTLExpression):
    def __init__(self, var: str, arg: SimpleTLExpression):
        super().__init__(is_state_goal=arg.is_state_goal)
        self.var = var
        self.arg = arg

    def __str__(self):
        return 'Forall({}, {})'.format(self.var, self.arg)

    def eval_state(self, state: State, action: Optional[Action], variable_mapping: Dict[str, str]) -> bool:
        variable_mapping = variable_mapping.copy()
        for obj in state.objects:
            variable_mapping[self.var] = obj
            if not self.arg.eval_state(state, action, variable_mapping):
                return False
        return True

    def eval(self, trajectory: StateActionSequence, variable_mapping: Dict[str, str]) -> EvaluationResult:
        if self.is_state_goal:
            for i, (s, a) in enumerate(trajectory.iter_sa_pairs()):
                if self.eval_state(s, a, variable_mapping):
                    return EvaluationResult(rv=True, shortest_prefix=i + 1)
            return EvaluationResult(rv=False, shortest_prefix=-1)
        else:
            variable_mapping = variable_mapping.copy()
            global_index = -1
            for obj in trajectory.states[0].objects:
                variable_mapping[self.var] = obj
                result = self.arg.eval(trajectory, variable_mapping)
                if not result.rv:
                    return EvaluationResult(rv=False, shortest_prefix=-1)
                global_index = max(global_index, result.shortest_prefix)
            return EvaluationResult(rv=True, shortest_prefix=global_index)

class SimpleTLForN(SimpleTLExpression):
    def __init__(self, n: int, var: str, arg: SimpleTLExpression):
        super().__init__(is_state_goal=arg.is_state_goal)
        self.n = n
        self.var = var
        self.arg = arg
    
    def __str__(self):
        return 'ForN({}, {}, {})'.format(self.n, self.var, self.arg)
    
    def eval_state(self, state: State, action: Optional[Action], variable_mapping: Dict[str, str]) -> bool:
        variable_mapping = variable_mapping.copy()
        count = 0
        for obj in state.objects:
            variable_mapping[self.var] = obj
            if self.arg.eval_state(state, action, variable_mapping):
                count += 1
        return count == self.n
    
    def eval(self, trajectory: StateActionSequence, variable_mapping: Dict[str, str]) -> EvaluationResult:
        if self.is_state_goal: # state goal
            for i, (s, a) in enumerate(trajectory.iter_sa_pairs()):
                if self.eval_state(s, a, variable_mapping):
                    return EvaluationResult(rv=True, shortest_prefix=i + 1)
            return EvaluationResult(rv=False, shortest_prefix=-1)
        else: # temporal goal
            # Below, we are trying to find the number of times the expression is satisfied in the trajectory
            variable_mapping = variable_mapping.copy()
            global_index = 1e9
            count = 0
            for obj in trajectory.states[0].objects:
                variable_mapping[self.var] = obj
                result = self.arg.eval(trajectory, variable_mapping)
                if result.rv:
                    global_index = min(global_index, result.shortest_prefix)
                    count += 1
            return EvaluationResult(rv=count == self.n, shortest_prefix=global_index)


# class SimpleTLForPairs(SimpleTLExpression):
#     def __init__(self, var1: str, var2: str, arg: SimpleTLExpression):
#         super().__init__(is_state_goal=arg.is_state_goal)
#         self.var1 = var1
#         self.var2 = var2
#         self.arg = arg
    
#     def __str__(self):
#         return 'ForPairs({}, {}, {})'.format(self.var1, self.var2, self.arg)
    
#     def eval_state(self, state: State, action: Optional[Action], variable_mapping: Dict[str, str]) -> bool:
#         # check if the expression is satisfied for all pairs of objects in the state
#         # note that, for each instance x0 of var1 and each instance x1 of var2, we do not require 
#         variable_mapping = variable_mapping.copy()
#         for obj1 in state.objects:
#             for obj2 in state.objects:
#                 variable_mapping[self.var1] = obj1
#                 variable_mapping[self.var2] = obj2
#                 if not self.arg.eval_state(state, action, variable_mapping):
#                     return False
                

class SimpleTLExists(SimpleTLExpression):
    def __init__(self, var: str, arg: SimpleTLExpression):
        super().__init__(is_state_goal=arg.is_state_goal)
        self.var = var
        self.arg = arg

    def __str__(self):
        return 'Exists({}, {})'.format(self.var, self.arg)

    def eval_state(self, state: State, action: Optional[Action], variable_mapping: Dict[str, str]) -> bool:
        variable_mapping = variable_mapping.copy()
        for obj in state.objects:
            variable_mapping[self.var] = obj
            if self.arg.eval_state(state, action, variable_mapping):
                return True
        return False

    def eval(self, trajectory: StateActionSequence, variable_mapping: Dict[str, str]) -> EvaluationResult:
        if self.is_state_goal:
            for i, (s, a) in enumerate(trajectory.iter_sa_pairs()):
                if self.eval_state(s, a, variable_mapping):
                    return EvaluationResult(rv=True, shortest_prefix=i + 1)
            return EvaluationResult(rv=False, shortest_prefix=-1)
        else:
            variable_mapping = variable_mapping.copy()
            global_index = 1e9
            for obj in trajectory.states[0].objects:
                variable_mapping[self.var] = obj
                result = self.arg.eval(trajectory, variable_mapping)
                if result.rv:
                    global_index = min(global_index, result.shortest_prefix)
            return EvaluationResult(rv=global_index < 1e9, shortest_prefix=global_index)


class SimpleTLThen(SimpleTLExpression):
    def __init__(self, *args: SimpleTLExpression):
        super().__init__(is_state_goal=False)
        self.args = args

    def __str__(self):
        return 'Then({})'.format(', '.join(map(str, self.args)))

    def eval(self, trajectory: StateActionSequence, variable_mapping: Dict[str, str]) -> EvaluationResult:
        longest_seq = trajectory
        used_prefix = 0
        for arg in self.args:
            result = arg.eval(trajectory.exclude_prefix(used_prefix), variable_mapping)
            if not result.rv:
                return EvaluationResult(rv=False, shortest_prefix=-1)
            used_prefix += result.shortest_prefix
        return EvaluationResult(rv=True, shortest_prefix=len(longest_seq.states))


def eval_simple_tl(expression: SimpleTLExpression, trajectory: StateActionSequence, variable_mapping: Optional[Dict[str, str]] = None) -> bool:
    if variable_mapping is None:
        variable_mapping = {}
    return expression.eval(trajectory, variable_mapping).rv


def eval_simple_tl_state(expression: SimpleTLExpression, state: State, action: Optional[Action] = None, variable_mapping: Optional[Dict[str, str]] = None) -> bool:
    if variable_mapping is None:
        variable_mapping = {}
    assert expression.is_state_goal, 'The expression should be a state goal.'
    return expression.eval_state(state, action, variable_mapping)

def extract_propositions_and_actions(expression: SimpleTLExpression, special_var_list: Optional[List[str]]=None) -> Tuple[List[Proposition], List[Action]]:
    '''
    Extract all propositions and actions from a simple temporal logic expression.
    For special connectives exists and forall, we replace all wildcard variables with a specific object, but detailed variables will not be changed.
    '''
    propositions = []
    actions = []

    if isinstance(expression, SimpleTLPrimitive):
        if special_var_list is not None:
            prop_or_action = expression.prop_or_action
            # replace special_var with '<wildcard>' for extracted proposition and action
            if expression.is_proposition:
                replaced_prop = Proposition(prop_or_action.name, [arg if arg not in special_var_list else '<wildcard>' for arg in prop_or_action.args])
                propositions.append(replaced_prop)
            elif expression.is_action:
                replaced_action = Action(prop_or_action.name, [arg if arg not in special_var_list else '<wildcard>' for arg in prop_or_action.args])
                actions.append(replaced_action)
        elif expression.is_proposition:
            propositions.append(expression.prop_or_action)
        elif expression.is_action:
            actions.append(expression.prop_or_action)
    elif isinstance(expression, (SimpleTLAnd, SimpleTLOr, SimpleTLNot, SimpleTLImplies, SimpleTLThen)):
        if hasattr(expression, 'args'):
            for arg in expression.args:
                sub_props, sub_actions = extract_propositions_and_actions(arg, special_var_list)
                propositions.extend(sub_props)
                actions.extend(sub_actions)
        elif hasattr(expression, 'arg'):
            sub_props, sub_actions = extract_propositions_and_actions(expression.arg, special_var_list)
            propositions.extend(sub_props)
            actions.extend(sub_actions)
        elif hasattr(expression, 'left') and hasattr(expression, 'right'):
            left_props, left_actions = extract_propositions_and_actions(expression.left, special_var_list)
            right_props, right_actions = extract_propositions_and_actions(expression.right, special_var_list)
            propositions.extend(left_props)
            propositions.extend(right_props)
            actions.extend(left_actions)
            actions.extend(right_actions)
    elif isinstance(expression, (SimpleTLForall, SimpleTLExists)):
        quantifier_var = expression.var
        prev_special_var_list = special_var_list if special_var_list is not None else []
        special_var_list = prev_special_var_list + [quantifier_var]
        sub_props, sub_actions = extract_propositions_and_actions(expression.arg, special_var_list)
        special_var_list = prev_special_var_list
        propositions.extend(sub_props)
        actions.extend(sub_actions)
    elif isinstance(expression, SimpleTLForN):
        quantifier_var = expression.var
        prev_special_var_list = special_var_list if special_var_list is not None else []
        special_var_list = prev_special_var_list + [quantifier_var]
        sub_props, sub_actions = extract_propositions_and_actions(expression.arg, special_var_list)
        special_var_list = prev_special_var_list
        propositions.extend(sub_props)
        actions.extend(sub_actions)
    return propositions, actions

def extract_args(expression: SimpleTLExpression) -> Set[str]:
    propositions, actions = extract_propositions_and_actions(expression)
    args = set()
    for prop in propositions:
        args.update(prop.args)
    for action in actions:
        args.update(action.args)
    # remove '<wildcard>' from args
    args.discard('<wildcard>')
    return args

def demorgan_expassion(expression: SimpleTLNot) -> SimpleTLExpression:
    '''Apply De Morgan's law to the expression.

    Args:
        expression: the expression to apply De Morgan's law.

    Returns:
        SimpleTLExpression: the expression after applying De Morgan's law.
    '''
    arg = expression.arg
    if isinstance(arg, SimpleTLPrimitive):
        return expression
    elif isinstance(arg, SimpleTLAnd):
        return SimpleTLOr(*[SimpleTLNot(sub_arg) for sub_arg in arg.args]) # not (a and b and c) = not a or not b or not c3
    elif isinstance(arg, SimpleTLOr):
        return SimpleTLAnd(*[SimpleTLNot(sub_arg) for sub_arg in arg.args]) # not (a or b or c) = not a and not b and not c
    elif isinstance(arg, SimpleTLNot):
        return arg.arg
    elif isinstance(arg, SimpleTLImplies):
        return SimpleTLAnd(arg.left, SimpleTLNot(arg.right)) # not (a -> b) = a and not b
    elif isinstance(arg, SimpleTLThen):
        raise ValueError('De Morgan\'s law is not applicable to temporal order.')
    elif isinstance(arg, SimpleTLForall):
        return SimpleTLExists(arg.var, SimpleTLNot(arg.arg)) # not forall x, P(x) = exists x, not P(x)
    elif isinstance(arg, SimpleTLExists):
        return SimpleTLForall(arg.var, SimpleTLNot(arg.arg)) # not exists x, P(x) = forall x, not P(x)
    elif isinstance(arg, SimpleTLForN):
        raise NotImplementedError('De Morgan\'s law is not implemented for ForN.')
    else:
        raise ValueError('Unknown expression type.')

def sample_a_determined_path_from_tl_expr(expression: SimpleTLExpression) -> List[Union[SimpleTLNot, SimpleTLPrimitive]]:
    cur_extracted_list = []
    if isinstance(expression, SimpleTLPrimitive):
        cur_extracted_list.append(expression)
    elif isinstance(expression, (SimpleTLThen, SimpleTLAnd)): # temporal order
        for arg in expression.args:
            cur_extracted_list.extend(sample_a_determined_path_from_tl_expr(arg))
    elif isinstance(expression, SimpleTLNot):
        expr = demorgan_expassion(expression)
        if isinstance(expr.arg, SimpleTLPrimitive):
            cur_extracted_list.append(expr)
        else:
            cur_extracted_list.extend(sample_a_determined_path_from_tl_expr(expr))
    elif isinstance(expression, SimpleTLOr):
        # randomly choose one of the arguments
        import random
        chosen_arg = random.choice(expression.args)
        cur_extracted_list.extend(sample_a_determined_path_from_tl_expr(chosen_arg))
    else:
        raise ValueError('Unknown expression type.')
    return cur_extracted_list



def test_extract_prop_actions():
    # expression_tree = SimpleTLThen(SimpleTLOr(SimpleTLAnd(SimpleTLPrimitive(Proposition('P', ['obj1'])), SimpleTLPrimitive(Proposition('Q', ['obj2']))), SimpleTLPrimitive(Proposition('S', ['obj4.4', 'obj5.5', 'obj6.6']))), SimpleTLPrimitive(Proposition('R', ['obj3'])))
    expression_tree = SimpleTLThen(SimpleTLForall("x", SimpleTLOr(SimpleTLPrimitive(Proposition('P1', ['x'])), SimpleTLExists('y', SimpleTLAnd(SimpleTLPrimitive(Proposition('P2', ['obj3', 'y'])), SimpleTLPrimitive(Action('Q1', ['x', 'y'])))))), SimpleTLPrimitive(Proposition('R1', ['obj1'])), SimpleTLExists('x', SimpleTLNot(SimpleTLPrimitive(Proposition('P3', ['x', 'y'])))))
    print(expression_tree)
    propositions, actions = extract_propositions_and_actions(expression_tree)

    print("Propositions:")
    for p in propositions:
        print(p)

    print("Actions:")
    for a in actions:
        print(a)

def test_simple_state():
    state = State(['a', 'b', 'c'], [
        Proposition('P', ['a']),
        Proposition('Q', ['b']),
        Proposition('R', ['c']),
    ])


    expression = SimpleTLPrimitive(Proposition('P', ['a']))
    assert eval_simple_tl_state(expression, state)  # P(a) is true

    expression = SimpleTLPrimitive(Proposition('Q', ['a']))
    assert not eval_simple_tl_state(expression, state)  # Q(a) is false

    expression = SimpleTLPrimitive(Proposition('Q', ['b']))
    assert eval_simple_tl_state(expression, state)  # Q(b) is true

    expression = SimpleTLForall('x', SimpleTLPrimitive(Proposition('P', ['x'])))
    assert not eval_simple_tl_state(expression, state)  # forall x, P(x) is false

    expression = SimpleTLExists('x', SimpleTLPrimitive(Proposition('Q', ['x'])))
    assert eval_simple_tl_state(expression, state)  # exists x, Q(x) is true

    expression = SimpleTLAnd(SimpleTLPrimitive(Proposition('P', ['a'])), SimpleTLPrimitive(Proposition('Q', ['b'])))
    assert eval_simple_tl_state(expression, state)  # P(a) and Q(b) is true

    expression = SimpleTLAnd(SimpleTLNot(SimpleTLPrimitive(Proposition('P', ['b']))), SimpleTLPrimitive(Proposition('Q', ['b'])))
    assert eval_simple_tl_state(expression, state)  # not P(b) and Q(b) is true

    action = Action('A', ['a'])

    expression = SimpleTLPrimitive(action)
    assert eval_simple_tl_state(expression, state, action)  # A(a) is true

    expression = SimpleTLPrimitive(Action('A', ['b']))
    assert not eval_simple_tl_state(expression, state, action)  # A(b) is false

    expression = SimpleTLExists('x', SimpleTLPrimitive(Action('A', ['x'])))
    assert eval_simple_tl_state(expression, state, action)  # exists x, A(x) is true

    expression = SimpleTLForall('x', SimpleTLPrimitive(Action('A', ['x'])))
    assert eval_simple_tl_state(expression, state, action)

    print('Simple state tests passed.')


def test_simple_trajectory():
    state1 = State(['a', 'b', 'c'], [Proposition('P', ['a']), Proposition('Q', ['b']), Proposition('R', ['c'])])
    action1 = Action('A', ['a'])
    state2 = State(['a', 'b', 'c'], [Proposition('P', ['b']), Proposition('Q', ['b']), Proposition('R', ['c'])])
    action2 = Action('A', ['b'])
    state3 = State(['a', 'b', 'c'], [Proposition('P', ['c']), Proposition('Q', ['b']), Proposition('R', ['b'])])

    trajectory = StateActionSequence([state1, state2, state3], [action1, action2])

    expression = SimpleTLPrimitive(Proposition('P', ['a']))
    assert eval_simple_tl(expression, trajectory)  # Eventually. P(a) is true

    expression = SimpleTLPrimitive(Proposition('P', ['b']))
    assert eval_simple_tl(expression, trajectory)  # P(b) is true

    expression = SimpleTLThen(SimpleTLPrimitive(Proposition('P', ['a'])), SimpleTLPrimitive(Proposition('P', ['b'])))
    assert eval_simple_tl(expression, trajectory)  # P(a) -> P(b) is true

    expression = SimpleTLThen(SimpleTLPrimitive(Proposition('P', ['b'])), SimpleTLPrimitive(Proposition('P', ['a'])))
    assert not eval_simple_tl(expression, trajectory)  # P(b) -> P(a) is false

    expression = SimpleTLAnd(
        SimpleTLAnd(SimpleTLPrimitive(Proposition('P', ['a'])), SimpleTLPrimitive(Proposition('Q', ['b']))),
        SimpleTLPrimitive(Action('A', ['a']))
    )  # There is a state where P(a) and Q(b) is true, and the action of that state is A(a).
    assert eval_simple_tl(expression, trajectory)

    expression = SimpleTLThen(
        SimpleTLAnd(SimpleTLPrimitive(Proposition('P', ['a'])), SimpleTLPrimitive(Proposition('Q', ['b']))),
        SimpleTLPrimitive(Action('A', ['a']))
    )  # There is a state where P(a) and Q(b) is true, and after that state-action pair, the action is A(a).
    assert not eval_simple_tl(expression, trajectory)

    expression = SimpleTLThen(
        SimpleTLAnd(SimpleTLPrimitive(Proposition('P', ['a'])), SimpleTLPrimitive(Proposition('Q', ['b']))),
        SimpleTLPrimitive(Action('A', ['b']))
    )  # There is a state where P(a) and Q(b) is true, and after that state-action pair, the action is A(b).
    assert eval_simple_tl(expression, trajectory)

    expression = SimpleTLThen(
        SimpleTLNot(SimpleTLPrimitive(Proposition('P', ['b']))),
        SimpleTLPrimitive(Action('A', ['b']))
    )  # There is a state where "not P(b)" is true, and after that state-action pair, the action is A(b).
    assert eval_simple_tl(expression, trajectory)

    print('Simple trajectory tests passed.')


def test_simple_tl_for_n():
    state1 = State(['a', 'b', 'c'], [Proposition('P', ['a']), Proposition('P', ['b']), Proposition('Q', ['b']), Proposition('R', ['c'])])
    action1 = Action('A', ['a'])
    state2 = State(['a', 'b', 'c'], [Proposition('P', ['b']), Proposition('Q', ['b']), Proposition('R', ['b'])])
    action2 = Action('A', ['b'])
    state3 = State(['a', 'b', 'c'], [Proposition('P', ['c']), Proposition('Q', ['b']), Proposition('R', ['b'])])

    trajectory = StateActionSequence([state1, state2, state3], [action1, action2])

    expression = SimpleTLForN(2, 'x', SimpleTLPrimitive(Proposition('P', ['x'])))
    assert eval_simple_tl(expression, trajectory)  # There are 2 states where P(x) is true

    expression = SimpleTLForN(2, 'x', SimpleTLPrimitive(Proposition('Q', ['x'])))
    assert not eval_simple_tl(expression, trajectory)  # There are not 2 states where Q(x) is true

    expression = SimpleTLForN(1, 'x', SimpleTLPrimitive(Action('A', ['x'])))
    assert eval_simple_tl(expression, trajectory)  # There are 2 states where A(x) is true
                              

    print('Simple temporal logic for N tests passed.')

if __name__ == '__main__':
    # test_extract_prop_actions()
    # test_simple_state()
    # test_simple_trajectory()
    test_simple_tl_for_n()


