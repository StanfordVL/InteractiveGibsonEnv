from collections import deque
import copy
import os
import json

from igibson import object_states
from igibson.evaluation.eval_subgoal_plan.tl_formula.simple_tl import SimpleTLExpression, Proposition, Action, SimpleTLNot, SimpleTLPrimitive
from typing import List, Dict, Any, Optional, Tuple, Union
from igibson.evolving_graph.evolving_graph import GraphState
from igibson.evolving_graph.eval_evolving_graph_env import EvalGraphEnv
from igibson.evolving_graph.evolving_graph import EvolvingGraph

class Stack:
    def __init__(self) -> None:
        self.container = deque()
    
    def push(self, val):
        self.container.append(val)
    
    def pop(self):
        return self.container.pop()
    
    def peek(self):
        return self.container[-1]
    
    def is_empty(self):
        return len(self.container) == 0
    
    def size(self):
        return len(self.container)
    
    def __len__(self):
        return len(self.container)
    
    def __str__(self) -> str:
        return str(self.container)
    

class StateActionTranslator:
    def __init__(self, subgoal_list: List[Union[SimpleTLNot, SimpleTLPrimitive]], action_env: EvolvingGraph) -> None:
        self.subgoal_list = subgoal_list
        self.action_env = action_env
        self.obj_name_to_obj = action_env.name_to_obj
        assert all(isinstance(subgoal, (SimpleTLPrimitive, SimpleTLNot)) for subgoal in self.subgoal_list), 'Subgoal list should only contain SimpleTLPrimitive or SimpleTLNot objects.'
    
    @staticmethod
    def translate_tl_obj_into_addressable_obj(tl_obj:str) -> str:
        addressable_obj = tl_obj.replace('.', '_')
        return addressable_obj
    
    @staticmethod
    def check_in_which_hand(obj, hand_state):
        obj = StateActionTranslator.translate_tl_obj_into_addressable_obj(obj)
        left_hand_holding = hand_state['left_hand']
        right_hand_holding = hand_state['right_hand']
        if left_hand_holding is not None and obj in left_hand_holding:
            return 'left'
        elif right_hand_holding is not None and obj in right_hand_holding:
            return 'right'
        return None
    
    def get_an_available_hand(self, hand_state):
        left_hand_holding = hand_state['left_hand']
        right_hand_holding = hand_state['right_hand']
        if right_hand_holding is None:
            return 'right'
        elif left_hand_holding is None:
            return 'left'
        else:
            return None
    
    def spare_righthand_empty(self, cur_hand_state: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
        hand = 'right'
        if cur_hand_state['right_hand'] is None:
            return hand, []
        args = [cur_hand_state['right_hand']]
        action_list = []
        release = self.craft_an_action('<hand>_RELEASE', args, hand)
        action_list.append(release)
        return hand, action_list

    def spare_lefthand_empty(self, cur_hand_state: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
        hand = 'left'
        if cur_hand_state['left_hand'] is None:
            return hand, []
        args = [cur_hand_state['left_hand']]
        action_list = []
        release = self.craft_an_action('<hand>_RELEASE', args, hand)
        action_list.append(release)
        return hand, action_list
    
    def get_parent_objs(self, tl_obj:str):
        '''Here is an exmple to show how to use this method:
        for parent_obj in self.get_parent_objs(tl_obj):
            ... # Do something with parent_obj

        This method is reserved for the future use.
        '''
        addr_obj = StateActionTranslator.translate_tl_obj_into_addressable_obj(tl_obj)
        cur_state = self.action_env.cur_state
        node = cur_state.relation_tree.get_node(addr_obj)
        while node.parent is not cur_state.relation_tree.root:
            parent_obj_name = node.parent.obj
            parent_obj = self.obj_name_to_obj[parent_obj_name]
            yield parent_obj # Return the object instance
            node = node.parent

    def get_clean_dusty_important_items(self, cur_hand_state: Dict[str, Any]):
        cur_state = self.action_env.cur_state
        important_list = []
        for inventory_obj_name in cur_hand_state.values():
            if inventory_obj_name is None:
                continue
            inventory_obj = self.obj_name_to_obj[inventory_obj_name]
            if object_states.CleaningTool in cur_state.graph.nodes[inventory_obj.name].keys():
                important_list.append(inventory_obj)
        return important_list
    
    def get_clean_stained_important_items(self, cur_hand_state: Dict[str, Any]):
        cur_state = self.action_env.cur_state
        important_list = []
        allowed_cleaners=["detergent"]
        for inventory_obj_name in cur_hand_state.values():
            if inventory_obj_name is None:
                continue
            inventory_obj = self.obj_name_to_obj[inventory_obj_name]

            properties = cur_state.graph.nodes[inventory_obj.name]
            if object_states.CleaningTool in properties.keys() and object_states.Soaked in properties.keys() and properties[object_states.Soaked]:
                important_list.append(inventory_obj)
            
            for cleaner in allowed_cleaners:
                if cleaner in inventory_obj.name:
                    important_list.append(inventory_obj)
        return important_list
    
    def get_slice_important_items(self, cur_hand_state: Dict[str, Any]):
        cur_state = self.action_env.cur_state
        important_list = []
        for inventory_obj_name in cur_hand_state.values():
            if inventory_obj_name is None:
                continue
            inventory_obj = self.obj_name_to_obj[inventory_obj_name]

            if hasattr(inventory_obj, 'states') and object_states.Slicer in cur_state.graph.nodes[inventory_obj.name].keys():
                important_list.append(inventory_obj)
        return important_list

    def spare_hand_not_important(self, cur_hand_state: Dict[str, Any], important_items: List[str]):
        left_hand_holding = cur_hand_state['left_hand']
        right_hand_holding = cur_hand_state['right_hand']
        if right_hand_holding is None:
            return 'right', []
        if left_hand_holding is None:
            return 'left', []
        if right_hand_holding not in important_items:
            return self.spare_righthand_empty(cur_hand_state)
        if left_hand_holding not in important_items:
            return self.spare_lefthand_empty(cur_hand_state)
        assert False, 'both hand holding important items!'

    @staticmethod
    def get_evgraph_format_args(arg_list:List[str]) -> str:
        arg_list = [StateActionTranslator.translate_tl_obj_into_addressable_obj(arg) for arg in arg_list]
        return ', '.join(arg_list)
    
    @staticmethod
    def get_evgraph_format_hand_action(action:str, hand:str) -> str:
        return action.replace('<hand>', hand.upper())
    
    @staticmethod
    def get_evgraph_format_action_instruction(action:str, args:str) -> Dict[str, str]:
        return {'action': action, 'object': args}
    
    def craft_an_action(self, wildcard_action:str, args:List[str], hand:Union[str, None]) -> Dict[str, str]:
        if hand is not None:
            evgraph_format_action = self.get_evgraph_format_hand_action(wildcard_action, hand)
        else:
            evgraph_format_action = wildcard_action
        evgraph_format_args = self.get_evgraph_format_args(args)
        action_instruction = self.get_evgraph_format_action_instruction(evgraph_format_action, evgraph_format_args)
        return action_instruction
    
    def grasp_obj(self, cur_hand_state, obj_to_grasp, prev_holding_state):
        assert prev_holding_state is None, f'{obj_to_grasp} is grasped by robot!'
        action_list = []
        hand_holding = self.get_an_available_hand(cur_hand_state)
        if hand_holding is None:
            hand_holding, release = self.spare_righthand_empty(cur_hand_state)
            action_list.extend(release)
        grasp_args = [obj_to_grasp]
        grasp = self.craft_an_action('<hand>_GRASP', grasp_args, hand_holding)
        action_list.append(grasp)
        return hand_holding, action_list
    
    def map_nextto_ontop_to_action(self, p1: SimpleTLPrimitive, p2: SimpleTLPrimitive) -> List[List[Dict[str, str]]]:
        ontop_list = ['ontop', 'onfloor']
        nextto_list = ['nextto', 'touching']
        if p2.prop_or_action.name in ontop_list and p1.prop_or_action.name in nextto_list:
            p1, p2 = p2, p1
        pred_1 = p1.prop_or_action
        pred_2 = p2.prop_or_action
        pred_1_name = pred_1.name
        pred_2_name = pred_2.name
        assert (pred_1_name in ontop_list and pred_2_name in nextto_list), 'Special primitives should be ontop and nextto.'
        p1_receivee = pred_1.args[0]
        p1_receiver = pred_1.args[1]
        p2_obj1 = pred_2.args[0]
        p2_obj2 = pred_2.args[1]
        assert p1_receivee in [p2_obj1, p2_obj2], 'The objects in the two predicates should be the same.'
        cur_hand_state = self.action_env.cur_state.robot_inventory
        action_set_1 = []
        hand_holding = self.check_in_which_hand(p1_receivee, cur_hand_state)
        if hand_holding is None:
            hand_holding, grasp_actions_list = self.grasp_obj(cur_hand_state, p1_receivee, None)
            action_set_1.extend(grasp_actions_list)
        nextto_arg = p2_obj1 if p1_receivee == p2_obj2 else p2_obj2
        nextto_ontop_args = [nextto_arg, p1_receiver]
        nextto_ontop_str = f'<hand>_PLACE_NEXTTO_ONTOP'
        nextto_ontop = self.craft_an_action(nextto_ontop_str, nextto_ontop_args, hand_holding)
        action_set_1.append(nextto_ontop)
        return [action_set_1]

    def map_positive_primitive_to_action(self, primitive:SimpleTLPrimitive) -> List[List[Dict[str, str]]]:
        action_set_candidates = []
        predicate = primitive.prop_or_action
        primitive_name = predicate.name
        cur_hand_state = self.action_env.cur_state.robot_inventory

        if primitive_name == 'inside':
            obj1 = predicate.args[0]
            obj2 = predicate.args[1]
            common_action_list = []
            hand_holding = self.check_in_which_hand(obj1, cur_hand_state)
            if hand_holding is None:
                hand_holding, grasp_actions_list = self.grasp_obj(cur_hand_state, obj1, None)
                common_action_list.extend(grasp_actions_list)
            inside_args = [obj2]
            action_set_1 = copy.deepcopy(common_action_list)
            place_inside_str = f'<hand>_PLACE_INSIDE'
            place_inside = self.craft_an_action(place_inside_str, inside_args, hand_holding)
            action_set_1.append(place_inside)

            action_set_2 = copy.deepcopy(common_action_list)
            transfer_str = f'<hand>_TRANSFER_CONTENTS_INSIDE'
            transfer = self.craft_an_action(transfer_str, inside_args, hand_holding)
            action_set_2.append(transfer)

            action_set_candidates.append(action_set_1)
            # action_set_candidates.append(action_set_2) # search budget is insufficient

        elif primitive_name == 'ontop' or primitive_name == 'onfloor':
            receivee = predicate.args[0]
            receiver = predicate.args[1]
            common_action_list = []
            hand_holding = self.check_in_which_hand(receivee, cur_hand_state)
            if hand_holding is None:
                hand_holding, grasp_actions_list = self.grasp_obj(cur_hand_state, receivee, None)
                common_action_list.extend(grasp_actions_list)
            ontop_args = [receiver]

            action_set_1 = copy.deepcopy(common_action_list)
            place_ontop_str = f'<hand>_PLACE_ONTOP'
            place_ontop = self.craft_an_action(place_ontop_str, ontop_args, hand_holding)
            action_set_1.append(place_ontop)
            
            action_set_2 = copy.deepcopy(common_action_list)
            transfer_str = f'<hand>_TRANSFER_CONTENTS_ONTOP'
            transfer = self.craft_an_action(transfer_str, ontop_args, hand_holding)
            action_set_2.append(transfer)

            action_set_candidates.append(action_set_1)
            # action_set_candidates.append(action_set_2) # search budget is insufficient

        elif primitive_name == 'nextto' or primitive_name == 'touching':
            obj1 = predicate.args[0]
            obj2 = predicate.args[1]
            common_action_list = []
            hand_holding = self.check_in_which_hand(obj1, cur_hand_state)
            if hand_holding is None:
                hand_holding, grasp_actions_list = self.grasp_obj(cur_hand_state, obj1, None)
                common_action_list.extend(grasp_actions_list)
            nextto_args = [obj2]
            nextto_str = f'<hand>_PLACE_NEXTTO'
            nextto = self.craft_an_action(nextto_str, nextto_args, hand_holding)
            common_action_list.append(nextto)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'under':
            obj1 = predicate.args[0]
            obj2 = predicate.args[1]
            common_action_list = []
            hand_holding = self.check_in_which_hand(obj1, cur_hand_state)
            if hand_holding is None:
                hand_holding, grasp_actions_list = self.grasp_obj(cur_hand_state, obj1, None)
                common_action_list.extend(grasp_actions_list)
            under_args = [obj2]
            under_str = f'<hand>_PLACE_UNDER'
            under = self.craft_an_action(under_str, under_args, hand_holding)
            common_action_list.append(under)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'cooked' or primitive_name == 'burnt':
            obj = predicate.args[0]
            common_action_list = []
            _, action_list = self.spare_hand_not_important(cur_hand_state, [])
            common_action_list.extend(action_list)
            cook_args = [obj]
            cook_str = f'COOK'
            cook = self.craft_an_action(cook_str, cook_args, None)
            common_action_list.append(cook)
            action_set_candidates.append(common_action_list)

        elif primitive_name == 'dusty':
            pass
        
        elif primitive_name == 'stained':
            pass

        elif primitive_name == 'frozen':
            obj = predicate.args[0]
            common_action_list = []
            _, action_list = self.spare_hand_not_important(cur_hand_state, [])
            common_action_list.extend(action_list)
            freeze_args = [obj]
            freeze_str = f'FREEZE'
            freeze = self.craft_an_action(freeze_str, freeze_args, None)
            common_action_list.append(freeze)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'open':
            obj = predicate.args[0]
            common_action_list = []
            _, action_list = self.spare_hand_not_important(cur_hand_state, [])
            common_action_list.extend(action_list)
            open_args = [obj]
            open_str = f'OPEN'
            open = self.craft_an_action(open_str, open_args, None)
            common_action_list.append(open)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'sliced':
            obj = predicate.args[0]
            common_action_list = []
            important_list = self.get_slice_important_items(cur_hand_state)
            _, action_list = self.spare_hand_not_important(cur_hand_state, important_list)
            common_action_list.extend(action_list)
            slice_args = [obj]
            slice_str = f'SLICE'
            slice = self.craft_an_action(slice_str, slice_args, None)
            common_action_list.append(slice)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'soaked':
            obj = predicate.args[0]
            common_action_list = []
            _, action_list = self.spare_hand_not_important(cur_hand_state, [])
            common_action_list.extend(action_list)
            soak_args = [obj]
            soak_str = f'SOAK'
            soak = self.craft_an_action(soak_str, soak_args, None)
            common_action_list.append(soak)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'toggledon':
            obj = predicate.args[0]
            common_action_list = []
            _, action_list = self.spare_hand_not_important(cur_hand_state, [])
            common_action_list.extend(action_list)
            toggleon_args = [obj]
            toggleon_str = f'TOGGLE_ON'
            toggleon = self.craft_an_action(toggleon_str, toggleon_args, None)
            common_action_list.append(toggleon)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'holds_rh':
            obj = predicate.args[0]
            common_action_list = []
            _, action_list = self.spare_righthand_empty(cur_hand_state)
            common_action_list.extend(action_list)
            hold_args = [obj]
            hold_str = f'RIGHT_GRASP'
            hold = self.craft_an_action(hold_str, hold_args, None)
            common_action_list.append(hold)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'holds_lh':
            obj = predicate.args[0]
            common_action_list = []
            _, action_list = self.spare_lefthand_empty(cur_hand_state)
            common_action_list.extend(action_list)
            hold_args = [obj]
            hold_str = f'LEFT_GRASP'
            hold = self.craft_an_action(hold_str, hold_args, None)
            common_action_list.append(hold)
            action_set_candidates.append(common_action_list)
        
        return action_set_candidates

    def map_negative_primitive_to_action(self, primitive:SimpleTLNot) -> List[List[Dict[str, str]]]:
        pos_arg = primitive.arg
        assert isinstance(pos_arg, SimpleTLPrimitive), 'The argument of a negative primitive should be a positive primitive.'
        action_set_candidates = []
        predicate = pos_arg.prop_or_action
        primitive_name = predicate.name
        cur_hand_state = self.action_env.cur_state.robot_inventory

        if primitive_name == 'inside':
            obj1 = predicate.args[0]
            obj2 = predicate.args[1]
            common_action_list = []
            hand_holding = self.check_in_which_hand(obj1, cur_hand_state)
            if hand_holding is None:
                hand_holding, grasp_actions_list = self.grasp_obj(cur_hand_state, obj1, None)
                common_action_list.extend(grasp_actions_list)
            right_release_args = [obj1]
            right_release_str = f'RIGHT_RELEASE'
            right_release = self.craft_an_action(right_release_str, right_release_args, None)
            common_action_list.append(right_release)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'ontop' or primitive_name == 'onfloor':
            # always are side effects
            return []
            obj1 = predicate.args[0]
            obj2 = predicate.args[1]
            common_action_list = []
            hand_holding = self.check_in_which_hand(obj1, cur_hand_state)
            if hand_holding is None:
                hand_holding, grasp_actions_list = self.grasp_obj(cur_hand_state, obj1, None)
                common_action_list.extend(grasp_actions_list)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'nextto' or primitive_name == 'touching':
            # always are side effects
            return []
            obj1 = predicate.args[0]
            obj2 = predicate.args[1]
            common_action_list = []
            hand_holding = self.check_in_which_hand(obj1, cur_hand_state)
            if hand_holding is None:
                hand_holding, grasp_actions_list = self.grasp_obj(cur_hand_state, obj1, None)
                common_action_list.extend(grasp_actions_list)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'under':
            # always are side effects
            return []
            obj1 = predicate.args[0]
            obj2 = predicate.args[1]
            common_action_list = []
            hand_holding = self.check_in_which_hand(obj1, cur_hand_state)
            if hand_holding is None:
                hand_holding, grasp_actions_list = self.grasp_obj(cur_hand_state, obj1, None)
                common_action_list.extend(grasp_actions_list)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'cooked' or primitive_name == 'burnt':
            pass

        elif primitive_name == 'dusty':
            obj = predicate.args[0]
            common_action_list = []
            important_list = self.get_clean_dusty_important_items(cur_hand_state)
            hand_holding, action_list = self.spare_hand_not_important(cur_hand_state, important_list)
            common_action_list.extend(action_list)
            clean_args = [obj]
            clean_str = f'CLEAN'
            clean = self.craft_an_action(clean_str, clean_args, hand_holding)
            common_action_list.append(clean)
            action_set_candidates.append(common_action_list)

        elif primitive_name == 'stained':
            obj = predicate.args[0]
            common_action_list = []
            important_list = self.get_clean_stained_important_items(cur_hand_state)
            hand_holding, action_list = self.spare_hand_not_important(cur_hand_state, important_list)
            common_action_list.extend(action_list)
            clean_args = [obj]
            clean_str = f'CLEAN'
            clean = self.craft_an_action(clean_str, clean_args, hand_holding)
            common_action_list.append(clean)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'frozen':
            obj = predicate.args[0]
            common_action_list = []
            _, action_list = self.spare_hand_not_important(cur_hand_state, [])
            common_action_list.extend(action_list)
            thaw_args = [obj]
            thaw_str = f'UNFREEZE'
            thaw = self.craft_an_action(thaw_str, thaw_args, None)
            common_action_list.append(thaw)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'open':
            obj = predicate.args[0]
            common_action_list = []
            _, action_list = self.spare_hand_not_important(cur_hand_state, [])
            common_action_list.extend(action_list)
            close_args = [obj]
            close_str = f'CLOSE'
            close = self.craft_an_action(close_str, close_args, None)
            common_action_list.append(close)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'sliced':
            pass

        elif primitive_name == 'soaked':
            pass

        elif primitive_name == 'toggledon':
            obj = predicate.args[0]
            common_action_list = []
            _, action_list = self.spare_hand_not_important(cur_hand_state, [])
            common_action_list.extend(action_list)
            toggleoff_args = [obj]
            toggleoff_str = f'TOGGLE_OFF'
            toggleoff = self.craft_an_action(toggleoff_str, toggleoff_args, None)
            common_action_list.append(toggleoff)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'holds_rh':
            obj = predicate.args[0]
            common_action_list = []
            hand_holding = self.check_in_which_hand(obj, cur_hand_state)
            if hand_holding == 'right':
                _, action_list = self.spare_righthand_empty(cur_hand_state)
                common_action_list.extend(action_list)
            action_set_candidates.append(common_action_list)
        
        elif primitive_name == 'holds_lh':
            obj = predicate.args[0]
            common_action_list = []
            hand_holding = self.check_in_which_hand(obj, cur_hand_state)
            if hand_holding == 'left':
                _, action_list = self.spare_lefthand_empty(cur_hand_state)
                common_action_list.extend(action_list)
            action_set_candidates.append(common_action_list)
        
        return action_set_candidates
    
    def get_primitive_name(self, p: Union[SimpleTLNot, SimpleTLPrimitive]) -> str:
        if isinstance(p, SimpleTLNot):
            assert isinstance(p.arg, SimpleTLPrimitive), 'The argument of a negative primitive should be a positive primitive.'
            return p.arg.prop_or_action.name
        return p.prop_or_action.name
    
    def check_nextto_ontop_to_action(self, p1: Union[SimpleTLNot, SimpleTLPrimitive], p2: Union[SimpleTLNot, SimpleTLPrimitive]) -> Tuple[bool, Any, Any]:
        if isinstance(p1, SimpleTLNot) or isinstance(p2, SimpleTLNot):
            return False, None, None
        ontop_list = ['ontop', 'onfloor']
        nextto_list = ['nextto', 'touching']
        pred_1 = p1.prop_or_action
        pred_2 = p2.prop_or_action
        pred_1_name = pred_1.name
        pred_2_name = pred_2.name
        pred_1_args = pred_1.args
        pred_2_args = pred_2.args
        if pred_1_name in ontop_list and pred_2_name in nextto_list:
            if pred_1_args[0] == pred_2_args[0] or pred_1_args[0] == pred_2_args[1]:
                return True, p1, p2
        elif pred_1_name in nextto_list and pred_2_name in ontop_list:
            if pred_1_args[0] == pred_2_args[0] or pred_1_args[1] == pred_2_args[0]:
                return True, p2, p1
        return False, None, None

    def map_subgoal_to_action_sequence_static_version(self) -> List[List[List[Dict[str, str]]]]:
        '''[Warning] the translation requires the dynamic information of the environment like states changed in hands, yet this is not provided in this method. This method is only for the static version of the translation.'''
        action_sequence = []
        subgoal_list_len = len(self.subgoal_list)
        next_read = True
        for i, primitive in enumerate(self.subgoal_list):
            if not next_read:
                next_read = True
                continue
            if i != subgoal_list_len - 1:
                next_pred = self.subgoal_list[i+1]
                if self.check_nextto_ontop_to_action(primitive, next_pred)[0]:
                    assert isinstance(primitive, SimpleTLPrimitive) and isinstance(next_pred, SimpleTLPrimitive), 'The two predicates should be SimpleTLPrimitive objects.'
                    action_sequence.append(self.map_nextto_ontop_to_action(primitive, next_pred))
                    next_read = False
                    continue
            if isinstance(primitive, SimpleTLPrimitive):
                action_sequence.append(self.map_positive_primitive_to_action(primitive))
            elif isinstance(primitive, SimpleTLNot):
                action_sequence.append(self.map_negative_primitive_to_action(primitive))
        return action_sequence

    def map_subgoal_to_action_sequence_dynamic_version(self, cur_primitive: Union[SimpleTLNot, SimpleTLPrimitive], next_primitive: Union[SimpleTLNot, SimpleTLPrimitive, None], new_action_env:EvolvingGraph) -> Tuple[bool, List[List[Dict[str, str]]]]:
        '''The dynamic version of the translation. This does not directly generate the complete action sequence, but requires the dynamic state infor to generate the latest action candidates for each primitive.
        
        Args:
        - cur_primitive: The current primitive to be translated.
        - next_primitive: The next primitive to be translated. If the current primitive is the last one, this should be None.
        - new_env: The new environment instance after the action is applied.
        
        Returns:
        - is combined states: A boolean value indicating whether the current primitive and the next primitive are combined states.
        - action_candidates: A list of action candidates for the current primitive. Each candidate is a list of actions that can be applied to the environment.
        '''
        self.action_env = new_action_env
        is_combined_states = False
        if next_primitive is not None:
            is_combined_states = self.check_nextto_ontop_to_action(cur_primitive, next_primitive)[0]
        if is_combined_states:
            action_candidates = self.map_nextto_ontop_to_action(cur_primitive, next_primitive)
        else:
            if isinstance(cur_primitive, SimpleTLPrimitive):
                action_candidates = self.map_positive_primitive_to_action(cur_primitive)
            elif isinstance(cur_primitive, SimpleTLNot):
                action_candidates = self.map_negative_primitive_to_action(cur_primitive)
        return is_combined_states, action_candidates