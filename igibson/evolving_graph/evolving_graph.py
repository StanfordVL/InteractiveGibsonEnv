import networkx as nx
from igibson.objects.multi_object_wrappers import ObjectMultiplexer,ObjectGrouper
from igibson import object_states
from igibson.objects.articulated_object import URDFObject
from igibson.transition_model.relation_tree import GraphRelationTree,TeleportType
from igibson.object_states.on_floor import RoomFloor
from igibson.tasks.behavior_task import BehaviorTask
from collections import deque
from enum import Enum, unique,auto
import sys, os
import copy
import os, sys

class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

UnaryStates=[
    object_states.Cooked,
    object_states.Dusty,
    object_states.Frozen,
    object_states.Open,
    object_states.Sliced,
    object_states.Soaked,
    object_states.Stained,
    object_states.ToggledOn,
    #object_states.Burnt,
    object_states.Slicer,
    object_states.CleaningTool,
    # object_states.HeatSourceOrSink,
    # object_states.WaterSource,

]

BinaryStates=[
    object_states.Inside,
    object_states.OnFloor,
    object_states.OnTop,
    #object_states.Touching,
    object_states.Under,
    object_states.NextTo,
]

NonTeleportBinaryStates=[
    object_states.OnFloor,
    #object_states.Touching,
    object_states.Under,
    object_states.NextTo,
]

TeleportBinaryStaets=[
    object_states.Inside,
    object_states.OnTop,
]

SPECIAL_NAME_MAPPING={"toggled_on":"toggledon",
                              }

class ErrorType(Enum):
    AFFORDANCE_ERROR=auto()
    MISSING_STEP=auto()
    ADDITIONAL_STEP=auto()
    WRONG_TEMPORAL_ORDER=auto()
    

class GraphState():
    def __init__(self,name_to_obj):
        self.relation_tree=GraphRelationTree(name_to_obj)
        self.graph=nx.DiGraph()
        self.robot_inventory = {'right_hand':None,'left_hand':None}

    def get_category_mapping(self,task:BehaviorTask):
        # map obj.name to category
        category_mapping={}
        for name, obj in task.object_scope.items():
            category="_".join(name.split("_")[:-1])
            if isinstance(obj, ObjectMultiplexer):
                category_mapping[obj.name.rstrip("_multiplexer")]=category
            elif isinstance(obj, RoomFloor) or isinstance(obj, URDFObject):
                category_mapping[obj.name]=category
        return category_mapping
    
    def get_all_inhand_objects(self,hand):
        inhand_objects=[]
        def traverse(node):
            inhand_objects.append(node.obj)
            for child in node.children.keys():
                inhand_objects.append(child)
                traverse(node.children[child])
        v=self.robot_inventory[hand]
        if v is not None:
            traverse(self.relation_tree.get_node(v))
        return set(inhand_objects)
    
    def get_name_mapping(self,task:BehaviorTask):
        # map bddl name to obj.name
        name_mapping={}
        for name, obj in task.object_scope.items():
            if isinstance(obj, ObjectMultiplexer):
                name_mapping[name]=obj.name.rstrip("_multiplexer")
            elif isinstance(obj, RoomFloor) or isinstance(obj, URDFObject):
                name_mapping[name]=obj.name
        return name_mapping
    
    def get_state_dict(self,task:BehaviorTask):
        """
                {
        "nodes": {name:{"name": name, "category": category, "states": set(states), "properties": set(properties)}},
        "edges": [{"from_name": name, "relation": relation, "to_name": name}]
        }
        """
        category_mapping=self.get_category_mapping(task)
        state_dict={"nodes":{},"edges":[]}
        for node_name in self.graph.nodes:
            name=node_name
            if '_part_' in node_name:
                name=node_name.split('_part_')[0]
                category=category_mapping[name]
            else:
                category=category_mapping[node_name]
            properties=set(state.__name__.lower() for state in self.graph.nodes[node_name].keys())
            relation_node=self.relation_tree.get_node(node_name)
            if relation_node is not None: # assume everything is graspable except floor
                properties.add("inhandofrobot")
                properties.add("inlefthandofrobot")
                properties.add("inrighthandofrobot")
            states=set([state.__name__.lower() for state in self.graph.nodes[node_name].keys() if self.graph.nodes[node_name][state]])
            if self.robot_inventory["left_hand"]==node_name:
                 states.add("inlefthandofrobot")
                 states.add("inhandofrobot")
            elif self.robot_inventory["right_hand"]==node_name:
                states.add("inrighthandofrobot")
                states.add("inhandofrobot")
            state_dict["nodes"][node_name]={"name":node_name,"category":category,"states":states,"properties":properties}
        for edge in self.graph.edges:
            from_name=edge[0]
            to_name=edge[1]
            relation=self.graph.edges[edge]["state"].__name__.lower()
            state_dict["edges"].append({"from_name":from_name,"relation":relation,"to_name":to_name})

        # add teleport relations
        for node_name in self.graph.nodes:
            cur_node=self.relation_tree.get_node(node_name)
            if cur_node is None or cur_node.parent is self.relation_tree.root:
                continue

            # for inside, consider all ancestors, for ontop, consider only parent
            if cur_node.teleport_type==TeleportType.ONTOP:
                state_dict["edges"].append({"from_name":cur_node.obj,"relation":"ontop","to_name":cur_node.parent.obj})
            elif cur_node.teleport_type==TeleportType.INSIDE:
                state_dict["edges"].append({"from_name":cur_node.obj,"relation":"inside","to_name":cur_node.parent.obj})
            next_node=cur_node.parent
            while next_node.parent is not self.relation_tree.root:
                if relation==TeleportType.INSIDE:
                    state_dict["edges"].append({"from_name":cur_node.obj,"relation":"inside","to_name":next_node.parent.obj})
                next_node=next_node.parent


        # update parts in state_dict
        for obj in state_dict["nodes"].keys():
            if "sliced" in state_dict["nodes"][obj]["states"] and "_part_" not in obj:
                part_0=obj+"_part_0"
                part_1=obj+"_part_1"
                assert part_0 in state_dict["nodes"] and part_1 in state_dict["nodes"]
                state_dict["nodes"][obj]["states"]=state_dict["nodes"][part_0]["states"].intersection(state_dict["nodes"][part_1]["states"])
                part_1_edges=set([(edge["relation"],edge["to_name"]) for edge in state_dict["edges"] if edge["from_name"]==part_1])
                part_0_edges=set([(edge["relation"],edge["to_name"]) for edge in state_dict["edges"] if edge["from_name"]==part_0])
                obj_edges=part_0_edges.intersection(part_1_edges)
                # delete all edges related to obj first
                state_dict["edges"]=[edge for edge in state_dict["edges"] if edge["from_name"]!=obj]
                for edge in list(obj_edges):
                    state_dict["edges"].append({"from_name":obj,"relation":edge[0],"to_name":edge[1]})
                    
        return state_dict
            
    def check_success(self,task:BehaviorTask):
        name_mapping=self.get_name_mapping(task)
        state_dict=self.get_state_dict(task)

        subgoals=[]
        subgoal_success=[]
        for cond in task.goal_conditions:
            subgoals.append(cond.terms)
            subgoal_options=cond.flattened_condition_options
            flag=False
            for subgoal_option in subgoal_options:
                flag=self._check_goal_combo(subgoal_option,name_mapping,state_dict)
                if flag:
                    break
            subgoal_success.append(flag)
        return {
            "success":all(subgoal_success),
            "subgoals":subgoals,
            "subgoal_success":subgoal_success
        }
                    

    def _check_goal_combo(self,goal_combo,name_mapping,state_dict):
        for goal in goal_combo:
            if not self._check_goal(goal,name_mapping,state_dict):
                return False
        return True
    
    def _check_goal(self,goal,name_mapping,state_dict):
        #remove inner [] in goal, only keep the first level
        def remove_inner_brackets(input_list):
            result = []
            for element in input_list:
                if isinstance(element, list):
                    result.extend(remove_inner_brackets(element))
                else:
                    result.append(element)
            return result
        goal=remove_inner_brackets(goal)
        if 'not' in goal:
            if not (len(goal)==3 or len(goal)==4):
                print(goal)
            assert len(goal)==3 or len(goal)==4
            if len(goal)==3:
                state=goal[1]
                node_name=name_mapping[goal[2]]
                if state in SPECIAL_NAME_MAPPING:
                    state=SPECIAL_NAME_MAPPING[state]
                assert state in state_dict["nodes"][node_name]['properties']
                return state not in state_dict["nodes"][node_name]['states']
            else:
                relation=goal[1]
                if relation in SPECIAL_NAME_MAPPING:
                    relation=SPECIAL_NAME_MAPPING[relation]
                from_name=name_mapping[goal[2]]
                to_name=name_mapping[goal[3]]
                for edge in state_dict['edges']:
                    if edge['from_name']==from_name and edge['to_name']==to_name and edge['relation']==relation:
                        return False
                return True
            
        else:
            if not (len(goal)==2 or len(goal)==3):
                print(goal)
            assert len(goal)==2 or len(goal)==3
            if len(goal)==2:
                state=goal[0]
                if state in SPECIAL_NAME_MAPPING:
                    state=SPECIAL_NAME_MAPPING[state]
                node_name=name_mapping[goal[1]]
                assert state in state_dict["nodes"][node_name]['properties']
                return state in state_dict["nodes"][node_name]['states']
            else:
                relation=goal[0]
                if relation in SPECIAL_NAME_MAPPING:
                    relation=SPECIAL_NAME_MAPPING[relation]
                from_name=name_mapping[goal[1]]
                to_name=name_mapping[goal[2]]
                for edge in state_dict['edges']:
                    if edge['from_name']==from_name and edge['to_name']==to_name and edge['relation']==relation:
                        return True
                return False
                

        

class EvolvingGraph():
    def __init__(self,addressable_objects):
        self.addressable_objects=addressable_objects
        self.name_to_obj={obj.name:obj for obj in addressable_objects}
        self.cur_state=GraphState(self.name_to_obj)
        self.history_states=[]
        self.build_graph()

    
  
    
    def add_node_with_attr(self,obj):
        self.cur_state.graph.add_node(obj.name)
        for state in obj.states.keys():
            if state in UnaryStates:
                self.cur_state.graph.nodes[obj.name][state]=obj.states[state].get_value()

    def build_graph(self):
        for obj in self.addressable_objects:
            self.add_node_with_attr(obj)
        for obj1 in self.addressable_objects:
            for obj2 in self.addressable_objects:
                for state in NonTeleportBinaryStates:
                    if obj1.states[state].get_value(obj2):
                        self.cur_state.graph.add_edge(obj1.name,obj2.name,state=state)
                        if state==object_states.NextTo:
                            self.cur_state.graph.add_edge(obj2.name,obj1.name,state=state)
        
## ---------------------------Action functions--------------------------------

    def check_precondition(self,precond):
        if not precond.check_precond(self.cur_state):
            for state in self.history_states:
                ## ignore print of the same error
                if precond.check_precond(state,ignore_print=True):
                    print(f"<Error> {ErrorType.WRONG_TEMPORAL_ORDER} <Reason> Temporal order is wrong")
                    return False
            return False
        return True
    


    def grasp(self,obj:URDFObject,hand:str):

        ## Precondition check
        class GraspPrecond(BasePrecond):
            def __init__(self,obj,hand,name_to_obj):
                super().__init__(obj,name_to_obj)
                self.precond_list.appendleft(self.grasp_precond)
                self.hand=hand
            
            def grasp_precond(self,state:GraphState):
                if isinstance(self.obj,RoomFloor):
                    print(f"<Error> {ErrorType.AFFORDANCE_ERROR} <Reason> Cannot grasp floor (GRASP)")
                    return False
                
                if self.obj.bounding_box[0]*self.obj.bounding_box[1]*self.obj.bounding_box[2]>1.5:
                    print(f"<Error> {ErrorType.AFFORDANCE_ERROR} <Reason> Object too big to grasp (GRASP)")
                    return False

                if state.robot_inventory[self.hand]==self.obj.name:
                    print(f"<Error> {ErrorType.ADDITIONAL_STEP} <Reason> Object already in hand (GRASP)")
                    return False
                
                if self.obj.name in state.robot_inventory.values():
                    print(f"<Error> {ErrorType.ADDITIONAL_STEP} <Reason> Object already in other hand (GRASP)")
                    return False
            
                if state.robot_inventory[self.hand] is not None:
                    print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Release first before grasp (GRASP)")
                    return False
                return True
            
        precond=GraspPrecond(obj,hand,self.name_to_obj)
        if not self.check_precondition(precond):
            return False
        

        ## Posteffect
        successors = list(self.cur_state.graph.successors(obj.name))
        predecessors = list(self.cur_state.graph.predecessors(obj.name))
        for successor in successors:
            self.cur_state.graph.remove_edge(obj.name,successor)
        for predecessor in predecessors:
            self.cur_state.graph.remove_edge(predecessor,obj.name)
        self.cur_state.robot_inventory[hand]=obj.name
        self.cur_state.relation_tree.remove_ancestor(obj.name)
        node=self.cur_state.relation_tree.get_node(obj.name)
        node_to_remove=[]
        obj_volumn=obj.bounding_box[0]*obj.bounding_box[1]*obj.bounding_box[2]
        # remove teleport relation if child is too big
        if node is not None:
            for child_name in node.children.keys():
                child_obj=self.name_to_obj[child_name]
                if child_obj.bounding_box[0]*child_obj.bounding_box[1]*child_obj.bounding_box[2]>5*obj_volumn:
                    node_to_remove.append(child_name)
        for child_name in node_to_remove:
            self.cur_state.relation_tree.remove_ancestor(child_name)
        print(f"Grasp {obj.name} success")
        return True

    def release(self,hand:str,obj=None):
        ## Precondition check
        class ReleasePrecond(BasePrecond):
            def __init__(self,obj,hand,name_to_obj):
                super().__init__(obj,name_to_obj)
                self.precond_list.appendleft(self.release_precond)
                self.hand=hand
            
            def release_precond(self,state:GraphState):
                if state.robot_inventory[self.hand] is None:
                    successors = list(state.graph.successors(self.obj.name))
                    predecessors = list(state.graph.predecessors(self.obj.name))
                    if len(successors)!=0 or len(predecessors)!=0:
                        print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Robot is not holding anything (RELEASE)")
                        return False
                    print(f"<Error> {ErrorType.ADDITIONAL_STEP} <Reason> Robot is not holding anything (RELEASE)")
                    return False
                if self.obj is not None and state.robot_inventory[self.hand]!=self.obj.name:
                    print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Robot is not holding target object (RELEASE)")
                    return False
                return True
            
        precond=ReleasePrecond(obj,hand,self.name_to_obj)
        if not self.check_precondition(precond):
            return False
        

        ## Posteffect
        self.cur_state.robot_inventory[hand]=None
        print(f"Release {obj.name} success")
        return True

    def place_inside(self,obj:URDFObject,hand:str):
        ## Precondition check
        class PlaceInsidePrecond(PlacePrecond):
            def __init__(self,obj,hand,name_to_obj):
                super().__init__(obj,hand,name_to_obj)
                self.precond_list.appendleft(self.place_inside_precond)
                self.obj=obj
                self.hand=hand
            
            def place_inside_precond(self,state:GraphState):
                obj_in_hand_name=state.robot_inventory[self.hand]
                if obj_in_hand_name is None:
                    return True
                obj_in_hand=self.name_to_obj[obj_in_hand_name]
                tar_obj=self.obj
                if obj_in_hand.bounding_box[0]*obj_in_hand.bounding_box[1]*obj_in_hand.bounding_box[2]>\
                tar_obj.bounding_box[0]*tar_obj.bounding_box[1]*tar_obj.bounding_box[2]:
                    print(f"<Error> {ErrorType.AFFORDANCE_ERROR} <Reason> Object too big to place inside target object (PLACE_INSIDE)")
                    return False
                
                if object_states.Open in state.graph.nodes[tar_obj.name].keys() and \
                not state.graph.nodes[tar_obj.name][object_states.Open]:
                    print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Target object is closed (PLACE_INSIDE)")
                    return False
                return True
        
        precond=PlaceInsidePrecond(obj,hand,self.name_to_obj)
        if not precond.check_precond(self.cur_state):
            return False
        
        ## Posteffect
        obj_in_hand_name=self.cur_state.robot_inventory[hand]
        obj_in_hand=self.name_to_obj[obj_in_hand_name]
        self.cur_state.relation_tree.change_ancestor(obj_in_hand.name,obj.name,TeleportType.INSIDE)
        self.cur_state.robot_inventory[hand]=None
        print(f"Place {obj_in_hand.name} inside {obj.name} success")
        return True
                

    def place_ontop(self,obj:URDFObject,hand:str):
        ## Precondition check
        precond=PlacePrecond(obj,hand,self.name_to_obj)
        if not precond.check_precond(self.cur_state):
            return False
        
        ## Posteffect
        obj_in_hand_name=self.cur_state.robot_inventory[hand]
        obj_in_hand=self.name_to_obj[obj_in_hand_name]
        self.cur_state.relation_tree.change_ancestor(obj_in_hand.name,obj.name,TeleportType.ONTOP)
        self.cur_state.robot_inventory[hand]=None
        print(f"Place {obj_in_hand.name} onto {obj.name} success")  
        return True




    def place_ontop_floor(self,obj,hand):
        ## Precondition check
        precond=PlacePrecond(obj,hand,self.name_to_obj)
        if not precond.check_precond(self.cur_state):
            return False
        
        ## Posteffect
        obj_in_hand_name=self.cur_state.robot_inventory[hand]
        obj_in_hand=self.name_to_obj[obj_in_hand_name]
        self.cur_state.graph.add_edge(obj_in_hand.name,obj.name,state=object_states.OnFloor)
        self.cur_state.robot_inventory[hand]=None
        print(f"Place {obj_in_hand.name} on floor {obj.name} success")
        return True
    
    def place_under(self,obj,hand):
        ## Precondition check
        precond=PlacePrecond(obj,hand,self.name_to_obj)
        if not precond.check_precond(self.cur_state):
            return False
        
        ## Posteffect
        obj_in_hand_name=self.cur_state.robot_inventory[hand]
        obj_in_hand=self.name_to_obj[obj_in_hand_name]
        self.cur_state.graph.add_edge(obj_in_hand.name,obj.name,state=object_states.Under)
        self.cur_state.robot_inventory[hand]=None

        node=self.cur_state.relation_tree.get_node(obj.name)
        if node is None:
            assert isinstance(obj,RoomFloor)
            self.cur_state.graph.add_edge(obj_in_hand.name,obj.name,state=object_states.OnFloor)
        else: # ontop or inside
            if node.parent is not self.cur_state.relation_tree.root:
                self.cur_state.relation_tree.change_ancestor(obj_in_hand.name,node.parent.obj,node.teleport_type)
            else: # onfloor
                successors = list(self.cur_state.graph.successors(obj.name))
                # find the edge with relation onfloor
                for successor in successors:
                    if self.cur_state.graph.edges[obj.name,successor]['state']==object_states.OnFloor:
                        self.cur_state.graph.add_edge(obj_in_hand.name,successor,state=object_states.OnFloor)
                        break
                    
        print(f"Place {obj_in_hand.name} under {obj.name} success")
        return True

    def place_next_to(self,obj,hand):
        ## Precondition check
        precond=PlacePrecond(obj,hand,self.name_to_obj)
        if not precond.check_precond(self.cur_state):
            return False
        
        ## Posteffect
        obj_in_hand_name=self.cur_state.robot_inventory[hand]
        obj_in_hand=self.name_to_obj[obj_in_hand_name]
        self.cur_state.graph.add_edge(obj.name,obj_in_hand.name,state=object_states.NextTo)
        self.cur_state.graph.add_edge(obj_in_hand.name,obj.name,state=object_states.NextTo)
        self.cur_state.robot_inventory[hand]=None

        node=self.cur_state.relation_tree.get_node(obj.name)
        if node is None:
            assert isinstance(obj,RoomFloor)
            self.cur_state.graph.add_edge(obj_in_hand.name,obj.name,state=object_states.OnFloor)
        else: # ontop or inside
            if node.parent is not self.cur_state.relation_tree.root:
                self.cur_state.relation_tree.change_ancestor(obj_in_hand.name,node.parent.obj,node.teleport_type)
            else: # onfloor
                successors = list(self.cur_state.graph.successors(obj.name))
                # find the edge with relation onfloor
                for successor in successors:
                    if self.cur_state.graph.edges[obj.name,successor]['state']==object_states.OnFloor:
                        self.cur_state.graph.add_edge(obj_in_hand.name,successor,state=object_states.OnFloor)
                        break
        print(f"Place {obj_in_hand.name} next to {obj.name} success")
        return True

    def place_next_to_ontop(self,tar_obj1:URDFObject,tar_obj2,hand:str):
        ## Precondition check
        precond1=PlacePrecond(tar_obj1,hand,self.name_to_obj)
        precond2=PlacePrecond(tar_obj2,hand,self.name_to_obj)
        if not precond1.check_precond(self.cur_state) or not precond2.check_precond(self.cur_state):
            return False
        
        
        ## Posteffect
        obj_in_hand_name=self.cur_state.robot_inventory[hand]
        obj_in_hand=self.name_to_obj[obj_in_hand_name]
        self.cur_state.graph.add_edge(obj_in_hand.name,tar_obj1.name,state=object_states.NextTo)
        self.cur_state.graph.add_edge(tar_obj1.name,obj_in_hand.name,state=object_states.NextTo)
        if not isinstance(tar_obj2,RoomFloor):
            self.cur_state.relation_tree.change_ancestor(obj_in_hand.name,tar_obj2.name,TeleportType.ONTOP)
        else:
            self.cur_state.graph.add_edge(obj_in_hand.name,tar_obj2.name,state=object_states.OnFloor)
        self.cur_state.robot_inventory[hand]=None
        print(f"Place {obj_in_hand.name} next to {tar_obj1.name} and onto {tar_obj2.name} success")
        return True

    def pour_inside(self,tar_obj:URDFObject,hand:str):
        ## Precondition check
        class PourInsidePrecond(PourPrecond):
            def __init__(self,obj,hand,name_to_obj):
                super().__init__(obj,hand,name_to_obj)
                self.precond_list.appendleft(self.pour_inside_precond)
                self.obj=obj
                self.hand=hand
                self.name_to_obj=name_to_obj
            
            def pour_inside_precond(self,state:GraphState):
                obj_in_hand_name=state.robot_inventory[self.hand]
                if obj_in_hand_name is None:
                    return True
                obj_in_hand=self.name_to_obj[obj_in_hand_name]
                tar_obj=self.obj
                
                
                for obj_inside_name in state.relation_tree.get_node(obj_in_hand.name).children.keys():
                    obj_inside=self.name_to_obj[obj_inside_name]
                    if obj_inside.bounding_box[0]*obj_inside.bounding_box[1]*obj_inside.bounding_box[2]> \
                    tar_obj.bounding_box[0]* tar_obj.bounding_box[1] * tar_obj.bounding_box[2]:
                        print(f"<Error> {ErrorType.AFFORDANCE_ERROR} <Reason> Object too big to pour inside target object (POUR_INSIDE)")
                        return False
                
                if object_states.Open in state.graph.nodes[tar_obj.name].keys() and \
                not state.graph.nodes[tar_obj.name][object_states.Open]:
                    print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Target object is closed (POUR_INSIDE)")
                    return False
                return True
            
        precond=PourInsidePrecond(tar_obj,hand,self.name_to_obj)
        if not precond.check_precond(self.cur_state):
            return False
        
        ## Posteffect
        obj_in_hand_name=self.cur_state.robot_inventory[hand]
        obj_in_hand=self.name_to_obj[obj_in_hand_name]
        for obj_inside_name in self.cur_state.relation_tree.get_node(obj_in_hand.name).children.keys():
            self.cur_state.relation_tree.change_ancestor(obj_inside_name,tar_obj.name,TeleportType.INSIDE)
        print(f"Pour {obj_in_hand.name} inside {tar_obj.name} success")
        return True
        


    def pour_onto(self,tar_obj:URDFObject,hand:str):
        ## Precondition check
        precond=PourPrecond(tar_obj,hand,self.name_to_obj)
        if not precond.check_precond(self.cur_state):
            return False
        
        ## Posteffect
        obj_in_hand_name=self.cur_state.robot_inventory[hand]
        obj_in_hand=self.name_to_obj[obj_in_hand_name]
        for obj_inside_name in self.cur_state.relation_tree.get_node(obj_in_hand.name).children.keys():
            obj_inside=self.name_to_obj[obj_inside_name]
            self.cur_state.relation_tree.change_ancestor(obj_inside.name,tar_obj.name,TeleportType.ONTOP)
        print(f"Pour {obj_in_hand.name} onto {tar_obj.name} success")
        return True
    
    #################high level actions#####################
    def open_or_close(self,obj:URDFObject,open_close:str):
        assert open_close in ['open','close']
        ## pre conditions
        class OpenClosePrecond(HighLevelActionPrecond):
            def __init__(self,obj,object_state,state_value,name_to_obj):
                super().__init__(obj,object_state,state_value,name_to_obj)
                self.precond_list.append(self.open_close_precond)
            def open_close_precond(self,state:GraphState):
                if self.state_value==True and object_states.ToggledOn in state.graph.nodes[self.obj.name].keys() and \
                state.graph.nodes[self.obj.name][object_states.ToggledOn]:
                    print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Object is toggled on, cannot open (OPEN)")
                    return False
                return True
            
        precond=OpenClosePrecond(obj,object_states.Open,open_close=='open',self.name_to_obj)
        if not self.check_precondition(precond):
            return False

        ## post effects
        print(f"{open_close} {obj.name} success")
        self.cur_state.graph.nodes[obj.name][object_states.Open]=(open_close=='open')
        return True
    
    def toggle_on_off(self,obj:URDFObject,on_off:str):
        assert on_off in ['on','off']
        ## pre conditions
        class ToggleOnOffPrecond(HighLevelActionPrecond):
            def __init__(self,obj,object_state,state_value,name_to_obj):
                super().__init__(obj,object_state,state_value,name_to_obj)
                self.precond_list.append(self.toggle_on_off_precond)
            def toggle_on_off_precond(self,state:GraphState):
                if self.state_value==True and object_states.Open in state.graph.nodes[self.obj.name].keys() and \
                state.graph.nodes[self.obj.name][object_states.Open]:
                    print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Object is open, close first to toggle on (TOGGLE_ON)")
                    return False
                return True
        precond=ToggleOnOffPrecond(obj,object_states.ToggledOn,on_off=='on',self.name_to_obj)
        if not self.check_precondition(precond):
            return False

        ## post effects
        self.cur_state.graph.nodes[obj.name][object_states.ToggledOn]=(on_off=='on')
        print(f"Toggle{on_off} {obj.name} success")


        # handel special effects, clean objects inside toggled on dishwasher
        allowed_cleaners=["dishwasher"]
        if on_off=='on':
            for allowed_cleaner in allowed_cleaners:
                if allowed_cleaner in obj.name:
                    for child_obj_name in self.cur_state.relation_tree.get_node(obj.name).children.keys():
                        if object_states.Dusty in self.cur_state.graph.nodes[child_obj_name].keys():
                            self.cur_state.graph.nodes[child_obj_name][object_states.Dusty]=False
                        if object_states.Stained in self.cur_state.graph.nodes[child_obj_name].keys():
                            self.cur_state.graph.nodes[child_obj_name][object_states.Stained]=False
                    print(f"Clean objects inside {obj.name} success")
                    break
        return True

    def slice(self,obj:URDFObject):
        ## pre conditions
        class SlicePrecond(HighLevelActionPrecond):
            def __init__(self,obj,object_state,state_value,name_to_obj):
                super().__init__(obj,object_state,state_value,name_to_obj)
                self.precond_list.appendleft(self.slice_precond)
            
            def slice_precond(self,state:GraphState):
                has_slicer=False
                for inventory_obj_name in state.robot_inventory.values():
                    if inventory_obj_name is None:
                        continue
                    inventory_obj=self.name_to_obj[inventory_obj_name]
                    
                    if hasattr(inventory_obj, "states") and object_states.Slicer in state.graph.nodes[inventory_obj.name].keys():
                        has_slicer=True
                        break
                if not has_slicer:
                    print(f"<Error> {ErrorType.MISSING_STEP} <Reason> No slicer in inventory (SLICE)")
                    return False
                return True
        
        precond=SlicePrecond(obj,object_states.Sliced,True,self.name_to_obj)
        if not self.check_precondition(precond):
            return False
    
        
        ## post effects
        self.cur_state.graph.nodes[obj.name][object_states.Sliced]=True
        obj_parts=[add_obj for add_obj in self.addressable_objects if '_part_' in add_obj.name and obj.name in add_obj.name]
        for part_obj in obj_parts:
            self.cur_state.graph.nodes[part_obj.name].update(self.cur_state.graph.nodes[obj.name])
        print(f"Slice {obj.name} success")

        ## update nonteleport relation
        successors = list(self.cur_state.graph.successors(obj.name))
        predecessors = list(self.cur_state.graph.predecessors(obj.name))


        for successor in successors:
            edge_state=self.cur_state.graph.edges[obj.name,successor]['state']
            self.cur_state.graph.remove_edge(obj.name,successor)
            for part_obj in obj_parts:
                self.cur_state.graph.add_edge(part_obj.name,successor,state=edge_state)
        for predecessor in predecessors:
            edge_state=self.cur_state.graph.edges[predecessor,obj.name]['state']
            self.cur_state.graph.remove_edge(predecessor,obj.name)
            for part_obj in obj_parts:
                self.cur_state.graph.add_edge(predecessor,part_obj.name,state=edge_state)

        ## update teleport relation
        obj_node=self.cur_state.relation_tree.get_node(obj.name)
        if obj_node.parent is not self.cur_state.relation_tree.root:
            parent_obj_name=obj_node.parent.obj
            parent_obj=self.name_to_obj[parent_obj_name]
            for part_obj in obj_parts:
                self.cur_state.relation_tree.change_ancestor(part_obj.name,parent_obj.name,obj_node.teleport_type)
            self.cur_state.relation_tree.remove_ancestor(obj.name)

        return True
    
    def clean_dust(self,obj):
        ## pre conditions
        class CleanDustPrecond(FullHandAllowedHighLevelPrecond):
            def __init__(self,obj,object_state,state_value,name_to_obj):
                super().__init__(obj,object_state,state_value,name_to_obj)
                self.precond_list.append(self.clean_dust_precond)
            
            def clean_dust_precond(self,state:GraphState):
                in_cleaner=False
                if not isinstance(self.obj,RoomFloor):
                    node=state.relation_tree.get_node(obj.name)
                    allowed_cleaners=["dishwasher","sink"]
                    while node.parent is not state.relation_tree.root:
                        parent_obj_name=node.parent.obj
                        parent_obj=self.name_to_obj[parent_obj_name]
                        if object_states.ToggledOn in state.graph.nodes[parent_obj.name].keys() \
                        and state.graph.nodes[parent_obj.name][object_states.ToggledOn]:
                            for allowed_cleaner in allowed_cleaners:
                                if allowed_cleaner in parent_obj.name:
                                    in_cleaner=True
                                    break
                        if in_cleaner:
                            break
                        node=node.parent
                 # check if cleaner in inventory
                has_cleaner=False
                for inventory_obj_name in state.robot_inventory.values():
                    if inventory_obj_name is None:
                        continue
                    inventory_obj=self.name_to_obj[inventory_obj_name]
                    
                    if object_states.CleaningTool in state.graph.nodes[inventory_obj.name].keys():
                        has_cleaner=True
                        break

                if not in_cleaner and not has_cleaner:
                    print(f"<Error> {ErrorType.MISSING_STEP} <Reason> No cleaner in inventory or object not in toggled on cleaner (CLEAN_DUST)")
                    return False
                
                return True
        precond=CleanDustPrecond(obj,object_states.Dusty,False,self.name_to_obj)
        if not self.check_precondition(precond):
            return False


        ## post effects
        self.cur_state.graph.nodes[obj.name][object_states.Dusty]=False
        print(f"Clean-dust {obj.name} success")
        return True
    
    def clean_stain(self,obj):
        ## pre conditions
        class CleanStainPrecond(FullHandAllowedHighLevelPrecond):
            def __init__(self,obj,object_state,state_value,name_to_obj):
                super().__init__(obj,object_state,state_value,name_to_obj)
                self.precond_list.append(self.clean_stain_precond)
            
            def clean_stain_precond(self,state:GraphState):
                in_cleaner=False
                if not isinstance(self.obj,RoomFloor):
                    node=state.relation_tree.get_node(obj.name)
                    allowed_cleaners=["sink"]
                    while node.parent is not state.relation_tree.root:
                        parent_obj_name=node.parent.obj
                        parent_obj=self.name_to_obj[parent_obj_name]
                        if object_states.ToggledOn in state.graph.nodes[parent_obj.name].keys() \
                        and state.graph.nodes[parent_obj.name][object_states.ToggledOn]:
                            for allowed_cleaner in allowed_cleaners:
                                if allowed_cleaner in parent_obj.name:
                                    in_cleaner=True
                                    break
                        if in_cleaner:
                            break
                        node=node.parent
                # check if has soaked cleaner in inventory
                has_soaked_cleaner=False
                allowed_cleaners=["detergent"]
                for inventory_obj_name in state.robot_inventory.values():
                    if inventory_obj_name is None:
                        continue
                    inventory_obj=self.name_to_obj[inventory_obj_name]
                    

                    if object_states.CleaningTool in state.graph.nodes[inventory_obj.name].keys() \
                    and object_states.Soaked in state.graph.nodes[inventory_obj.name].keys() \
                    and state.graph.nodes[inventory_obj.name][object_states.Soaked]:
                        has_soaked_cleaner=True
                        break
                        

                    for allowed_cleaner in allowed_cleaners:
                        if allowed_cleaner in inventory_obj.name:
                            has_soaked_cleaner=True
                            break

                    
                    if  has_soaked_cleaner:
                        break

                if not in_cleaner and not has_soaked_cleaner:
                    print(f"<Error> {ErrorType.MISSING_STEP} <Reason> No soaked cleaner in inventory or object not in toggled on cleaner (CLEAN_STAIN)")
                    return False
                
                return True
                
        precond=CleanStainPrecond(obj,object_states.Stained,False,self.name_to_obj)
        if not self.check_precondition(precond):
            return False
        
        ## post effects
        self.cur_state.graph.nodes[obj.name][object_states.Stained]=False
        print(f"Clean-stain {obj.name} success")
        return True
    
    def soak_dry(self,obj,soak_or_dry:str):
        ## pre conditions
        class soakDryPrecond(HighLevelActionPrecond):
            def __init__(self,obj,object_state,state_value,name_to_obj):
                super().__init__(obj,object_state,state_value,name_to_obj)
                self.precond_list.append(self.soak_dry_precond)
            
            def soak_dry_precond(self,state:GraphState):
                # if soak_or_dry=='soak', obj must be put in a toggled sink
                allowed_soakers=["sink","teapot"]
                if self.state_value==True:
                    in_sink=False
                    node=state.relation_tree.get_node(obj.name)
                    while node.parent is not state.relation_tree.root:
                        parent_obj_name=node.parent.obj
                        parent_obj=self.name_to_obj[parent_obj_name]
                        for allowed_soaker in allowed_soakers:
                            if allowed_soaker in parent_obj.name and (object_states.ToggledOn in state.graph.nodes[parent_obj.name].keys() \
                            and state.graph.nodes[parent_obj.name][object_states.ToggledOn] or \
                            object_states.ToggledOn not in state.graph.nodes[parent_obj.name].keys()):
                                in_sink=True
                                break
                        if in_sink:
                            break
                        node=node.parent
                    if not in_sink:
                        print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Object not in toggled on sink or in a teapot(SOAK)")
                        return False
                    
                return True       
        precond=soakDryPrecond(obj,object_states.Soaked,soak_or_dry=='soak',self.name_to_obj)
        if not self.check_precondition(precond):
            return False
        ## post effects
        self.cur_state.graph.nodes[obj.name][object_states.Soaked]=(soak_or_dry=='soak')
        print(f"{soak_or_dry.capitalize()} {obj.name} success")
        return True
    
    def freeze_unfreeze(self,obj,freeze_or_unfreeze:str):
        assert freeze_or_unfreeze in ['freeze','unfreeze']
        ## pre conditions
        precond=HighLevelActionPrecond(obj,object_states.Frozen,freeze_or_unfreeze=='freeze',self.name_to_obj)
        if not self.check_precondition(precond):
            return False
        
        ## post effects
        self.cur_state.graph.nodes[obj.name][object_states.Frozen]=(freeze_or_unfreeze=='freeze')
        print(f"{freeze_or_unfreeze.capitalize()} {obj.name} success")
        return True
    
    def cook(self,obj):
        ## pre conditions
        class CookPrecond(HighLevelActionPrecond):
            def __init__(self,obj,object_state,state_value,name_to_obj):
                super().__init__(obj,object_state,state_value,name_to_obj)
                self.precond_list.append(self.cook_precond)
            
            def cook_precond(self,state:GraphState):
                in_cooker=False
                allowered_cookers=["saucepan"]
                node=state.relation_tree.get_node(obj.name)
                while node.parent is not state.relation_tree.root:
                    parent_obj_name=node.parent.obj
                    parent_obj=self.name_to_obj[parent_obj_name]
                    for allowered_cooker in allowered_cookers:
                        if allowered_cooker in parent_obj.name:
                            in_cooker=True
                            break
                    if in_cooker:
                        break
                    node=node.parent
                if not in_cooker:
                    print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Object not in a cooker (COOK)")
                    return False
                return True
            
        precond=CookPrecond(obj,object_states.Cooked,True,self.name_to_obj)
        if not self.check_precondition(precond):
            return False
        
        ## post effects
        self.cur_state.graph.nodes[obj.name][object_states.Cooked]=True
        print(f"Cook {obj.name} success")
        return True
    ##################### for behavior task eval #####################    
    def left_grasp(self,obj:URDFObject):
        return self.grasp(obj,'left_hand')
    
    def right_grasp(self,obj:URDFObject):
        return self.grasp(obj,'right_hand')
    
    def left_release(self,obj:URDFObject):
        return self.release('left_hand',obj)
    
    def right_release(self,obj:URDFObject):
        return self.release('right_hand',obj)
    
    def left_place_ontop(self,obj):
        if isinstance(obj,RoomFloor):
            return self.place_ontop_floor(obj,'left_hand')
        else:
            return self.place_ontop(obj,'left_hand')
        
    def right_place_ontop(self,obj):
        if isinstance(obj,RoomFloor):
            return self.place_ontop_floor(obj,'right_hand')
        else:
            return self.place_ontop(obj,'right_hand')
    
    def left_place_inside(self,obj:URDFObject):
        return self.place_inside(obj,'left_hand')
    
    def right_place_inside(self,obj:URDFObject):
        return self.place_inside(obj,'right_hand')
    
    def open(self,obj:URDFObject):
        return self.open_or_close(obj,'open')
    
    def close(self,obj:URDFObject):
        return self.open_or_close(obj,'close')
    
    def left_place_nextto(self,obj:URDFObject):
        return self.place_next_to(obj,'left_hand')
    
    def right_place_nextto(self,obj:URDFObject):
        return self.place_next_to(obj,'right_hand')
    
    def left_transfer_contents_inside(self,obj:URDFObject):
        return self.pour_inside(obj,'left_hand')
    
    def right_transfer_contents_inside(self,obj:URDFObject):
        return self.pour_inside(obj,'right_hand')
    
    def left_transfer_contents_ontop(self,obj:URDFObject):
        return self.pour_onto(obj,'left_hand')
    
    def right_transfer_contents_ontop(self,obj:URDFObject):
        return self.pour_onto(obj,'right_hand')
    
    def soak(self,obj:URDFObject):
        return self.soak_dry(obj,'soak')
    
    def dry(self,obj:URDFObject):
        return self.soak_dry(obj,'dry')
    
    def freeze(self,obj:URDFObject):
        return self.freeze_unfreeze(obj,'freeze')
    
    def unfreeze(self,obj:URDFObject):
        return self.freeze_unfreeze(obj,'unfreeze')
    
    def toggle_on(self,obj:URDFObject):
        return self.toggle_on_off(obj,'on')
    
    def toggle_off(self,obj:URDFObject):
        return self.toggle_on_off(obj,'off')
    
    
    def left_place_nextto_ontop(self,obj1:URDFObject,obj2):
        return self.place_next_to_ontop(obj1,obj2,'left_hand')
    
    def right_place_nextto_ontop(self,obj1:URDFObject,obj2):
        return self.place_next_to_ontop(obj1,obj2,'right_hand')
    
    def left_place_under(self,obj:URDFObject):
        return self.place_under(obj,'left_hand')
    
    def right_place_under(self,obj:URDFObject):
        return self.place_under(obj,'right_hand')
    
    def clean(self,obj):

        if object_states.Dusty not in self.cur_state.graph.nodes[obj.name] and \
        object_states.Stained not in self.cur_state.graph.nodes[obj.name]:
            print(f"<Error> {ErrorType.AFFORDANCE_ERROR} <Reason> Object does not have target state (CLEAN)")
            return False

        # clean will clean both dust and stain
        try_clean_dust=False
        try_clean_stain=False
        flag1=False
        flag2=False
        if object_states.Dusty in self.cur_state.graph.nodes[obj.name] and self.cur_state.graph.nodes[obj.name][object_states.Dusty]==True:
            flag1=self.clean_dust(obj)
            try_clean_dust=True
        if object_states.Stained in self.cur_state.graph.nodes[obj.name] and self.cur_state.graph.nodes[obj.name][object_states.Stained]==True:
            flag2=self.clean_stain(obj)
            try_clean_stain=True
        if not (try_clean_dust or try_clean_stain):
            print(f"<Error> {ErrorType.ADDITIONAL_STEP} <Reason> Object is not dusty or stained (CLEAN)")
            return False
        return flag1 or flag2

    
class BasePrecond:
    def __init__(self,obj,name_to_obj):
        self.precond_list=deque()
        self.precond_list.append(self.interactivity_precond)
        self.obj=obj
        self.name_to_obj=name_to_obj
    
    def check_precond(self,state:GraphState,ignore_print=False):
        for precond in self.precond_list:
            if ignore_print:
                with HiddenPrints():
                    if not precond(state):
                        return False
            else:
                if not precond(state):
                    return False
        return True
    
    def interactivity_precond(self,state:GraphState):
        if isinstance(self.obj,RoomFloor):
            return True
        node=state.relation_tree.get_node(self.obj.name)
        while node.parent is not state.relation_tree.root:
            parent_obj_name=node.parent.obj
            parent_obj=self.name_to_obj[parent_obj_name]
            if (object_states.Open in state.graph.nodes[parent_obj.name].keys() and 
            not state.graph.nodes[parent_obj.name][object_states.Open] and
            node.teleport_type==TeleportType.INSIDE):
                print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Object is inside a closed object")
                return False
            node=node.parent

        if object_states.Sliced in state.graph.nodes[self.obj.name].keys() and \
        state.graph.nodes[self.obj.name][object_states.Sliced] and 'part' not in self.obj.name:
            print(f"<Error> {ErrorType.AFFORDANCE_ERROR} <Reason> Object is sliced, you need to interact with parts of it")
            return False

        return True


class PlacePrecond(BasePrecond):
    def __init__(self,obj,hand,name_to_obj):
        super().__init__(obj,name_to_obj)
        self.precond_list.appendleft(self.place_precond)
        self.hand=hand
        self.obj=obj
    
    def place_precond(self,state:GraphState):
        if state.robot_inventory[self.hand] is None:
            print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Robot is not holding anything (PLACE)")
            return False
        
        if self.obj==self.name_to_obj[state.robot_inventory[self.hand]]:
            print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Release target obj first before place (PLACE)")
            return False
        
        if self.obj.name in state.get_all_inhand_objects(self.hand):
            print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Release target obj first before place (PLACE)")
            return False
        return True

class PourPrecond(PlacePrecond):
    def __init__(self,obj,hand,name_to_obj):
        super().__init__(obj,hand,name_to_obj)
        self.precond_list.appendleft(self.pour_precond)
    
    def pour_precond(self,state:GraphState):
        in_hand_objs=state.get_all_inhand_objects(self.hand)
        if len(in_hand_objs)==1:
            print(f"<Error> {ErrorType.AFFORDANCE_ERROR} <Reason> Only holding one obj in {self.hand}, nothing to pour")
            return False
        return True
    
class HighLevelActionPrecond(BasePrecond):
    def __init__(self,obj,object_state,state_value,name_to_obj):
        super().__init__(obj,name_to_obj)
        self.precond_list.appendleft(self.high_level_action_precond)
        self.object_state=object_state
        self.state_value=state_value
    
    def high_level_action_precond(self,state:GraphState):
        if state.robot_inventory['right_hand'] is not None and state.robot_inventory['left_hand'] is not None:
            print(f"<Error> {ErrorType.MISSING_STEP} <Reason> Robot's both hands are full (HIGH_LEVEL_ACTION)")
            return False
        if self.object_state not in state.graph.nodes[self.obj.name]:
            print(f"<Error> {ErrorType.AFFORDANCE_ERROR} <Reason> Object does not have target state (HIGH_LEVEL_ACTION)")
            return False
        if state.graph.nodes[self.obj.name][self.object_state]==self.state_value:
            print(f"<Error> {ErrorType.ADDITIONAL_STEP} <Reason> Object's state is already satisfied (HIGH_LEVEL_ACTION)")
            return False
        return True
    
class FullHandAllowedHighLevelPrecond(BasePrecond):
    def __init__(self,obj,object_state,state_value,name_to_obj):
        super().__init__(obj,name_to_obj)
        self.precond_list.appendleft(self.high_level_action_precond)
        self.object_state=object_state
        self.state_value=state_value
    
    def high_level_action_precond(self,state:GraphState):
        if self.object_state not in state.graph.nodes[self.obj.name]:
            print(f"<Error> {ErrorType.AFFORDANCE_ERROR} <Reason> Object does not have target state (HIGH_LEVEL_ACTION)")
            return False
        if state.graph.nodes[self.obj.name][self.object_state]==self.state_value:
            print(f"<Error> {ErrorType.ADDITIONAL_STEP} <Reason> Object's state is already satisfied (HIGH_LEVEL_ACTION)")
            return False
        return True