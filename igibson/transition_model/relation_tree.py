from igibson.objects.articulated_object import URDFObject
from collections import defaultdict
import igibson.object_states as object_states
from enum import IntEnum, unique,auto
from abc import abstractmethod
from typing import Optional
# To teleport the relationship of inside
@unique
class TeleportType(IntEnum):
    ONTOP=auto()
    INSIDE=auto()
    

class RelationNode:
    def __init__(self, obj):
        self.obj = obj
        self.children = {}
        self.parent = None
        self.teleport_type=None

    def remove_node(self, other):
        self.children.pop(other.obj)

    def add_node(self, other,teleport_type:Optional[TeleportType]=None):
        other.teleport_type=teleport_type
        self.children[other.obj] = other
        other.parent = self

    def __hash__(self) -> int:
        return hash(self.obj)

class BaseRelationTree:
    @abstractmethod
    def _is_ancestor(self,obj1,obj2)->Optional[TeleportType]:
        pass
    
    def get_successor_dict(self,obj_list):
        successor_dict=dict()
        for obj1 in obj_list:
            successor_dict[obj1]=set()
            for obj2 in obj_list:
                if obj1 == obj2:
                    continue
                successor_type=self._is_ancestor(obj1,obj2)
                if successor_type is not None:
                    successor_dict[obj1].add(obj2)
                    if obj2 in successor_dict:
                        assert obj1 not in successor_dict[obj2]
        return successor_dict
    
    def get_relation_tree(self,obj_list):
        successor_dict=self.get_successor_dict(obj_list)
        # get the hierarchy of the tree
        hierarchy = []
        i=0
        while len(successor_dict)>0:
            cur_level = []
            for k,v in successor_dict.items():
                if len(v)!=0:
                    continue
                node=RelationNode(k)
                self.obj_to_node[k]=node
                cur_level.append(node)
            for v in successor_dict.values():
                for node in cur_level:
                    if node.obj in v:
                        v.remove(node.obj)
            for node in cur_level:
                successor_dict.pop(node.obj)
            hierarchy.append(cur_level) 


        if len(hierarchy)==0:
            return
        
        leaf_nodes=[node for node in hierarchy[0]]

        # build the tree, add links for each level
        for cur_level in hierarchy[1:]:
            new_leaf_nodes=[]
            for node_1 in leaf_nodes:
                picked_up=False
                for node_2 in cur_level:
                    if self._is_ancestor(node_2.obj,node_1.obj) is not None:
                        node_2.add_node(node_1)
                        picked_up=True
                        break
                if not picked_up:
                    new_leaf_nodes.append(node_1)
            leaf_nodes=new_leaf_nodes
            for node in cur_level:
                leaf_nodes.append(node)

        for node in leaf_nodes:
            self.root.add_node(node)


    def get_teleport_type(self)->None:
        def traverse(node):
            for child in node.children.values():
                teleport_type=self._is_ancestor(node.obj,child.obj)
                child.teleport_type=teleport_type
                traverse(child)
        traverse(self.root)

    def __init__(self,obj_list) -> None:
        self.root = RelationNode(None)
        self.obj_to_node={}
        self.get_relation_tree(obj_list)
        self.get_teleport_type()

    

    
    
class IgibsonRelationTree(BaseRelationTree):
    def _is_ancestor(self,obj1,obj2)->Optional[TeleportType]:
        if not isinstance(obj1, URDFObject) or not isinstance(obj2, URDFObject):
            return None
        if obj2.states[object_states.Inside].get_value(obj1):
            return TeleportType.INSIDE
        if obj2.states[object_states.OnTop].get_value(obj1):
            return TeleportType.ONTOP
        return None
    
    def __init__(self,obj_list) -> None:
        new_obj_list=[obj for obj in obj_list if isinstance(obj, URDFObject)]            
        super().__init__(new_obj_list)

    def get_node(self,obj)->RelationNode:
        return self.obj_to_node.get(obj,None)
    
    def change_ancestor(self,obj1,obj2,telport_type:TeleportType):
        node1=self.get_node(obj1)
        node2=self.get_node(obj2)
        node1.parent.remove_node(node1)
        node2.add_node(node1,telport_type)

    def remove_ancestor(self,obj):
        node=self.get_node(obj)
        parent=node.parent
        parent.remove_node(node)
        self.root.add_node(node)

    def __str__(self) -> str:
        def print_tree(node:RelationNode,level):
            res=""
            for i in range(level):
                res+="  "
            
            if node.obj is None:
                res+="root\n"
            else:
                res+=str(node.obj.name)+' '+str(node.teleport_type)+'\n'
            for child in node.children.values():
                res+=print_tree(child,level+1)
            return res
        return print_tree(self.root,0)


class GraphRelationTree(BaseRelationTree):
    def _is_ancestor(self,obj1:str,obj2:str)->Optional[TeleportType]:
        if self.teleport_relation_dict[obj2].get(obj1) == TeleportType.INSIDE:
            return TeleportType.INSIDE
        if self.teleport_relation_dict[obj2].get(obj1) == TeleportType.ONTOP:
            return TeleportType.ONTOP
        return None
    
    def __init__(self,name_to_obj:dict) -> None:
        new_obj_list=[obj.name for obj in name_to_obj.values() if isinstance(obj, URDFObject)]
        self.teleport_relation_dict=defaultdict(dict)
        for obj1_name in new_obj_list:
            for obj2_name in new_obj_list:
                if obj1_name == obj2_name:
                    continue
                obj1=name_to_obj[obj1_name]
                obj2=name_to_obj[obj2_name]
                if obj1.states[object_states.Inside].get_value(obj2):
                    self.teleport_relation_dict[obj1_name][obj2_name]=TeleportType.INSIDE
                if obj1.states[object_states.OnTop].get_value(obj2):
                    self.teleport_relation_dict[obj1_name][obj2_name]=TeleportType.ONTOP
        super().__init__(new_obj_list)
    
    def get_node(self,obj:str)->RelationNode:
        return self.obj_to_node.get(obj,None)
    
    def change_ancestor(self,obj1:str,obj2:str,telport_type:TeleportType):
        node1=self.get_node(obj1)
        node2=self.get_node(obj2)
        node1.parent.remove_node(node1)
        node2.add_node(node1,telport_type)

    def remove_ancestor(self,obj:str):
        node=self.get_node(obj)
        parent=node.parent
        parent.remove_node(node)
        self.root.add_node(node)

    def __str__(self) -> str:
        def print_tree(node:RelationNode,level):
            res=""
            for i in range(level):
                res+="  "
            
            if node.obj is None:
                res+="root\n"
            else:
                res+=str(node.obj)+' '+str(node.teleport_type)+'\n'
            for child in node.children.values():
                res+=print_tree(child,level+1)
            return res
        return print_tree(self.root,0)


        
    



    