import gym
import numpy as np
from igibson.action_primitives.starter_semantic_action_primitives import ActionPrimitiveError
from igibson.robots import BaseRobot,BehaviorRobot
from igibson.scenes.igibson_indoor_scene import InteractiveIndoorScene
import igibson.object_states as object_states
from igibson.object_states.on_floor import RoomFloor
from igibson.simulator import Simulator
from igibson.objects.object_base import BaseObject
from igibson.objects.articulated_object import URDFObject
from collections import defaultdict
from pyquaternion import Quaternion
from .relation_tree import IgibsonRelationTree
from .position_geometry import PositionGeometry
from .relation_tree import TeleportType
class ActionEnv:
    def __init__(
        self,
        simulator:Simulator,
        scene: InteractiveIndoorScene,
        robot: BehaviorRobot,
        addressable_objects:list,
        using_kinematics=False
    ):
        self.simulator = simulator
        self.scene = scene
        self.robot = robot
        self.addressable_objects = addressable_objects
        self.robot_inventory = {'right_hand':None,'left_hand':None}
        self.relation_tree=IgibsonRelationTree(self.addressable_objects) # to teleport relationship
        self.position_geometry=PositionGeometry(self.robot,simulator,using_kinematics)
        self.openable_objects = {obj:obj.states[object_states.Open].get_value() 
                                 for obj in self.addressable_objects if object_states.Open in obj.states}

    ##################### helper functions #####################

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
    
    def navigate_to_if_needed(self,obj:URDFObject):
        if not obj.states[object_states.InReachOfRobot].get_value():
            self.navigate_to(obj)

    def teleport_relation(self,obj1:URDFObject):
        teleport_func={
            TeleportType.INSIDE:self.position_geometry.set_inside,
            TeleportType.ONTOP:self.position_geometry.set_ontop,
        }
        obj_node=self.relation_tree.get_node(obj1)
        def recursive_teleport(node):
            for child in node.children.values():
                flag=teleport_func[child.teleport_type](child.obj,node.obj)
                print(f"Teleport {child.obj.name} {child.teleport_type.name} {node.obj.name} successful: {flag}")
                recursive_teleport(child)
        recursive_teleport(obj_node)

    def teleport_all(self):
        for obj in self.openable_objects.keys():
            obj.states[object_states.Open].set_value(self.openable_objects[obj],fully=True)
        self.simulator.step()
        for obj in self.relation_tree.root.children.keys():
            self.teleport_relation(obj)
        

    def check_interactability(self,obj1):
        # currently just checking if object is inside a closed object or not
        if isinstance(obj1,RoomFloor):
            return
        node=self.relation_tree.get_node(obj1)
        while node.parent is not self.relation_tree.root:
            parent_obj=node.parent.obj
            if (parent_obj in self.openable_objects and 
            not self.openable_objects[parent_obj] and
            node.teleport_type==TeleportType.INSIDE):
                raise ValueError(f"{obj1.name} is inside closed {parent_obj.name}")
            node=node.parent

    ##################### primitive actions #####################

    def navigate_to(self,obj):
        ## pre conditions   
        ## currently do auto navigation, no need for pre conditions
        ## post effects
        if obj.states[object_states.InReachOfRobot].get_value():
            return True
        
        if isinstance(obj,RoomFloor):
            self.position_geometry._set_robot_floor_magic(obj)
        else:
            self.position_geometry.set_robot_pos_for_obj(obj)
        for hand,invent_obj in self.robot_inventory.items():
            if invent_obj is not None:
                self.position_geometry.set_in_hand(invent_obj,hand)
                self.teleport_relation(invent_obj)

        if obj.states[object_states.InReachOfRobot].get_value():
            print(f"navigated to {obj.name}, InReachOfRobot: {obj.states[object_states.InReachOfRobot].get_value()}")
            return True
        
    def grasp(self,obj:URDFObject,hand:str):
        ## pre conditions
        try:
            self.check_interactability(obj)
        except ValueError as e:
            print(e)
            return False
        if self.robot_inventory[hand] is not None:
            print(f"{hand} is already holding {self.robot_inventory[hand].name}")
            return False
        # precondition for fixed body or volume?
        ## post effects
        self.navigate_to_if_needed(obj)
        self.relation_tree.remove_ancestor(obj)
        self.position_geometry.set_in_hand(obj,hand)
        self.robot_inventory[hand]=obj

        # remove all children of obj if they are too big
        node=self.relation_tree.get_node(obj)
        obj_volumn=obj.bounding_box[0]*obj.bounding_box[1]*obj.bounding_box[2]
        node_to_remove=[]
        if node is not None:
            for child_obj in node.children.keys():
                if child_obj.bounding_box[0]*child_obj.bounding_box[1]*child_obj.bounding_box[2]>5*obj_volumn:
                    teleport_relation=node.children[child_obj].teleport_type
                    print(f"Remove {child_obj.name} {teleport_relation.name} {obj.name} because it's too big")
                    node_to_remove.append(child_obj)
        for child_obj in node_to_remove:
            self.relation_tree.remove_ancestor(child_obj)
        self.teleport_relation(obj)
        print(f"Grasp {obj.name} with {hand} successful")
        return True
    
    def release(self,hand:str,obj=None):
        ## pre conditions
        if self.robot_inventory[hand] is None:
            print(f"{hand} is empty")
            return False
        if obj is not None and self.robot_inventory[hand]!=obj:
            print(f"{obj.name} is not in {hand}")
            return False
        ## post effects
        obj=self.robot_inventory[hand]
        self.robot_inventory[hand]=None
        self.position_geometry.release_obj(obj)
        self.teleport_relation(obj)
        print(f"Release {obj.name} from {hand} successful")
        return True
    
    def place_inside(self,tar_obj:URDFObject,hand:str):
        ## pre conditions
        try:
            self.check_interactability(tar_obj)
        except ValueError as e:
            print(e)
            return False
        
        if tar_obj in self.openable_objects and not self.openable_objects[tar_obj]:
            print(f"{tar_obj.name} is closed")
            return False
        
        if self.robot_inventory[hand] is None:
            print(f"{hand} is empty")
            return False
        
        in_hand_objs=self.get_all_inhand_objects(hand)
        obj_in_hand=self.robot_inventory[hand]
        if tar_obj in in_hand_objs:
            print(f"{tar_obj.name} is already in {hand}")
            return False
        
        if obj_in_hand.bounding_box[0]*obj_in_hand.bounding_box[1]*obj_in_hand.bounding_box[2]> \
        tar_obj.bounding_box[0]* tar_obj.bounding_box[1] * tar_obj.bounding_box[2]:
            print(f"{obj_in_hand.name} is bigger than {tar_obj.name}")
            return False
        
        ## post effects
        self.navigate_to_if_needed(tar_obj)
        self.relation_tree.change_ancestor(obj_in_hand,tar_obj,TeleportType.INSIDE)
        self.position_geometry.set_inside(obj_in_hand,tar_obj)
        self.teleport_relation(obj_in_hand)
        self.robot_inventory[hand]=None
        if obj_in_hand.states[object_states.Inside].get_value(tar_obj):
            print(f"Place inside {obj_in_hand.name} {tar_obj.name} successful")
            return True
        else:
            print(f"Place inside {obj_in_hand.name} {tar_obj.name} unsuccessful")
            return False
        
    def place_ontop_floor(self,obj:RoomFloor,hand:str):
        if self.robot_inventory[hand] is None:
            print(f"{hand} is empty")
            return False
        
        self.position_geometry._set_robot_floor_magic(obj)
        obj_in_hand=self.robot_inventory[hand]
        self.relation_tree.remove_ancestor(obj_in_hand)
        self.position_geometry._set_ontop_floor_magic(obj_in_hand,obj)
        self.teleport_relation(obj_in_hand)
        self.robot_inventory[hand]=None
        if obj_in_hand.states[object_states.OnFloor].get_value(obj):
            print(f"Place ontop {obj_in_hand.name} {obj.name} successful")
            return True
        else:
            print(f"Place ontop {obj_in_hand.name} {obj.name} unsuccessful")
            return False
        


    def place_ontop(self,obj:URDFObject,hand:str):
        ## pre conditions
        try:
            self.check_interactability(obj)
        except ValueError as e:
            print(e)
            return False
        
        if self.robot_inventory[hand] is None:
            print(f"{hand} is empty")
            return False
        
        in_hand_objs=self.get_all_inhand_objects(hand)
        obj_in_hand=self.robot_inventory[hand]
        if obj in in_hand_objs:
            print(f"{obj.name} is already in {hand}")
            return False

        
        ## post effects
        self.navigate_to_if_needed(obj)
        self.relation_tree.change_ancestor(obj_in_hand,obj,TeleportType.ONTOP)
        self.position_geometry.set_ontop(obj_in_hand,obj)
        self.teleport_relation(obj_in_hand)
        self.robot_inventory[hand]=None
        if obj_in_hand.states[object_states.OnTop].get_value(obj):
            print(f"Place ontop {obj_in_hand.name} {obj.name} successful")
            return True
        else:
            print(f"Place ontop {obj_in_hand.name} {obj.name} unsuccessful")
            return False
        
    def place_under(self,tar_obj:URDFObject,hand:str):
        ## pre conditions
        try:
            self.check_interactability(tar_obj)
        except ValueError as e:
            print(e)
            return False
        
        if self.robot_inventory[hand] is None:
            print(f"{hand} is empty")
            return False
        
        in_hand_objs=self.get_all_inhand_objects(hand)
        obj_in_hand=self.robot_inventory[hand]
        if tar_obj in in_hand_objs:
            print(f"{tar_obj.name} is already in {hand}")
            return False
        elif tar_obj in self.robot_inventory.values():
            print(f"Release {tar_obj.name} first to place {obj_in_hand.name} under it")
            return False
        
        ## post effects
        self.navigate_to_if_needed(tar_obj)
        self.relation_tree.remove_ancestor(obj_in_hand)
        self.position_geometry.set_under(obj_in_hand,tar_obj)
        self.teleport_relation(obj_in_hand)
        self.robot_inventory[hand]=None
        if obj_in_hand.states[object_states.Under].get_value(tar_obj):
            print(f"Place under {obj_in_hand.name} {tar_obj.name} successful")
            return True
        else:
            print(f"Place under {obj_in_hand.name} {tar_obj.name} unsuccessful")
            return False
        
    def place_next_to(self,tar_obj:URDFObject,hand:str):
        ## pre conditions
        try:
            self.check_interactability(tar_obj)
        except ValueError as e:
            print(e)
            return False
        
        if self.robot_inventory[hand] is None:
            print(f"{hand} is empty")
            return False
        
        in_hand_objs=self.get_all_inhand_objects(hand)
        obj_in_hand=self.robot_inventory[hand]
        if tar_obj in in_hand_objs:
            print(f"{tar_obj.name} is already in {hand}")
            return False
        elif tar_obj in self.robot_inventory.values():
            print(f"Release {tar_obj.name} first to place {obj_in_hand.name} next to it")
            return False
        
        ## post effects
        self.navigate_to_if_needed(tar_obj)
        if isinstance(tar_obj,RoomFloor):
            self.relation_tree.remove_ancestor(obj_in_hand)
        else:
            node=self.relation_tree.get_node(tar_obj)
            if node.parent is not self.relation_tree.root:
                self.relation_tree.change_ancestor(obj_in_hand,node.parent.obj,node.teleport_type)
            else:
                self.relation_tree.remove_ancestor(obj_in_hand)
        self.position_geometry.set_next_to(obj_in_hand,tar_obj)
        self.teleport_relation(obj_in_hand)
        self.robot_inventory[hand]=None
        if obj_in_hand.states[object_states.NextTo].get_value(tar_obj):
            print(f"Place next to {obj_in_hand.name} {tar_obj.name} successful")
            return True
        else:
            print(f"Place next to {obj_in_hand.name} {tar_obj.name} unsuccessful")
            return False
    
    def place_next_to_ontop(self,tar_obj1:URDFObject,tar_obj2,hand:str):
        ## pre conditions
        try:
            self.check_interactability(tar_obj1)
            self.check_interactability(tar_obj2)
        except ValueError as e:
            print(e)
            return False
        
        if self.robot_inventory[hand] is None:
            print(f"{hand} is empty")
            return False
        
        in_hand_objs=self.get_all_inhand_objects(hand)
        obj_in_hand=self.robot_inventory[hand]
        if tar_obj1 in in_hand_objs:
            print(f"{tar_obj1.name} is already in {hand}")
            return False
        elif tar_obj1 in self.robot_inventory.values():
            print(f"Release {tar_obj1.name} first to place {obj_in_hand.name} nextto it")
            return False
        
        if tar_obj2 in in_hand_objs:
            print(f"{tar_obj2.name} is already in {hand}")
            return False
        elif tar_obj2 in self.robot_inventory.values():
            print(f"Release {tar_obj2.name} first to place {obj_in_hand.name} ontop it")
            return False
        
        

        if isinstance(tar_obj2,RoomFloor):
            tar_state=object_states.OnFloor
            self.relation_tree.remove_ancestor(obj_in_hand)
        else:
            tar_state=object_states.OnTop
            self.relation_tree.change_ancestor(obj_in_hand,tar_obj2,TeleportType.ONTOP)

        ## post effects
        self.navigate_to_if_needed(tar_obj1)
        self.position_geometry._set_next_to_and_ontop_magic(obj_in_hand,tar_obj1,tar_obj2)
        self.teleport_relation(obj_in_hand)
        self.robot_inventory[hand]=None
        if obj_in_hand.states[object_states.NextTo].get_value(tar_obj1) and obj_in_hand.states[tar_state].get_value(tar_obj2):
            print(f"Place next to {obj_in_hand.name} {tar_obj1.name} on top of {tar_obj2.name} successful")
            return True
        else:
            print(f"Place next to {obj_in_hand.name} {tar_obj1.name} on top of {tar_obj2.name} unsuccessful")
            return False

    def pour_inside(self,tar_obj:URDFObject,hand:str):
        ## pre conditions
        try:
            self.check_interactability(tar_obj)
        except ValueError as e:
            print(e)
            return False
        
        if self.robot_inventory[hand] is None:
            print(f"{hand} is empty")
            return False
        
        obj_in_hand=self.robot_inventory[hand]
        if obj_in_hand==tar_obj:
            print(f"{tar_obj.name} is already in {hand}")
            return False
        elif tar_obj in self.robot_inventory.values():
            print(f"Release {tar_obj.name} first to pour contents in {obj_in_hand.name} inside it")
            return False
        
        if len(self.relation_tree.get_node(obj_in_hand).children)==0:
            print(f"{obj_in_hand.name} is empty, nothing to pour inside {tar_obj.name}")
            return False
        
        for obj_inside in self.relation_tree.get_node(obj_in_hand).children.keys():
            if obj_inside.bounding_box[0]*obj_inside.bounding_box[1]*obj_inside.bounding_box[2]> \
            tar_obj.bounding_box[0]* tar_obj.bounding_box[1] * tar_obj.bounding_box[2]:
                print(f"{obj_inside.name} is bigger than {tar_obj.name}, cannot pour inside")
                return False
        
        ## post effects
        self.navigate_to_if_needed(tar_obj)
        for obj_inside in self.relation_tree.get_node(obj_in_hand).children.keys():
            self.relation_tree.change_ancestor(obj_inside,tar_obj,TeleportType.INSIDE)
            self.position_geometry.set_inside(obj_inside,tar_obj)
            self.teleport_relation(obj_inside)
        print(f"Pour inside {obj_in_hand.name} {tar_obj.name} successful")
        return True
    
    def pour_onto(self,tar_obj:URDFObject,hand:str):
        ## pre conditions
        try:
            self.check_interactability(tar_obj)
        except ValueError as e:
            print(e)
            return False
        
        if self.robot_inventory[hand] is None:
            print(f"{hand} is empty")
            return False
        
        obj_in_hand=self.robot_inventory[hand]
        if obj_in_hand==tar_obj:
            print(f"{tar_obj.name} is already in {hand}")
            return False
        elif tar_obj in self.robot_inventory.values():
            print(f"Release {tar_obj.name} first to pour contents in {obj_in_hand.name} onto it")
            return False
        
        if len(self.relation_tree.get_node(obj_in_hand).children)==0:
            print(f"{obj_in_hand.name} is empty, nothing to pour onto {tar_obj.name}")
            return False
        
        ## post effects
        self.navigate_to_if_needed(tar_obj)
        for obj_inside in self.relation_tree.get_node(obj_in_hand).children.keys():
            self.relation_tree.change_ancestor(obj_inside,tar_obj,TeleportType.ONTOP)
            self.position_geometry.set_ontop(obj_inside,tar_obj)
            self.teleport_relation(obj_inside)
        print(f"Pour onto {obj_in_hand.name} {tar_obj.name} successful")
        return True
    
    ##################### high level actions #####################
    def open_or_close(self,obj:URDFObject,open_close:str):
        assert open_close in ['open','close']
        ## pre conditions
        try:
            self.check_interactability(obj)
        except ValueError as e:
            print(e)
            return False
        
        if object_states.Open not in obj.states:
            print(f"{obj.name} cannot be {open_close}ed")
            return False
        
        if self.openable_objects[obj]==(open_close=='open'):
            print(f"{obj.name} is already {open_close}ed")
            return False
        
        if None not in self.robot_inventory.values():
            print(f"Both hands full, release one object first to {open_close} the object")
            return False

        # can't open if toggled on
        if open_close=='open' and object_states.ToggledOn in obj.states and obj.states[object_states.ToggledOn].get_value():
            print(f"{obj.name} is toggled on, cannot be opened")
            return False

        ## post effects
        self.navigate_to_if_needed(obj)
        flag=obj.states[object_states.Open].set_value((open_close=='open'),fully=True)
        self.openable_objects[obj]=(open_close=='open')
        if obj.states[object_states.Open].get_value()==(open_close=='open'):
            print(f"{open_close.capitalize()} {obj.name} success")
            return True
        else:
            print(f"{open_close.capitalize()} {obj.name} failed")
            return False
    
    def toggle_on_off(self,obj:URDFObject,on_off:str):
        assert on_off in ['on','off']
        ## pre conditions
        try:
            self.check_interactability(obj)
        except ValueError as e:
            print(e)
            return False
        
        if object_states.ToggledOn not in obj.states:
            print(f"{obj.name} cannot be toggled {on_off}")
            return False
        
        if obj.states[object_states.ToggledOn].get_value()==(on_off=='on'):
            print(f"{obj.name} is already toggled {on_off}")
            return False
        
        if None not in self.robot_inventory.values():
            print(f"Both hands full, release one object first to toggle {on_off} the object")
            return False

        # can't toggle on if open
        if on_off=='on' and object_states.Open in obj.states and obj.states[object_states.Open].get_value():
            print(f"{obj.name} is open, cannot be toggled on")
            return False

        ## post effects
        self.navigate_to_if_needed(obj)
        
        obj.states[object_states.ToggledOn].set_value((on_off=='on'))
        print(f"Toggle{on_off} {obj.name} success")


        # handel special effects, clean objects inside toggled on dishwasher
        allowed_cleaners=["dishwasher"]
        if on_off=='on':
            for allowed_cleaner in allowed_cleaners:
                if allowed_cleaner in obj.name:
                    for child in self.relation_tree.get_node(obj).children.values():
                        if object_states.Dusty in child.obj.states:
                            child.obj.states[object_states.Dusty].set_value(False)
                        if object_states.Stained in child.obj.states:
                            child.obj.states[object_states.Stained].set_value(False)
                    print(f"Clean objects inside {obj.name} success")
                    break
        return True

    def slice(self,obj:URDFObject):
        ## pre conditions
        try:
            self.check_interactability(obj)
        except ValueError as e:
            print(e)
            return False
        
        if not (hasattr(obj, "states") and object_states.Sliced in obj.states):
            print("Slice failed, object cannot be sliced")
            return False
        
        if obj.states[object_states.Sliced].get_value():
            print("Slice failed, object is already sliced")
            return False
        
        has_slicer=False
        for inventory_obj in self.robot_inventory.values():
            if inventory_obj is None:
                continue
            if hasattr(inventory_obj, "states") and object_states.Slicer in inventory_obj.states:
                has_slicer=True
                break
        if not has_slicer:
            print("Slice failed, no slicer in inventory")
            return False
        
        ## post effects
        self.navigate_to_if_needed(obj)
        obj.states[object_states.Sliced].set_value(True)
        print(f"Slice {obj.name} success")

        obj_parts=[add_obj for add_obj in self.addressable_objects if 'part' in add_obj.name and obj.name in add_obj.name]
        obj_node=self.relation_tree.get_node(obj)
        if obj_node.parent is not self.relation_tree.root:
            parent_obj=obj_node.parent.obj
            for part_obj in obj_parts:
                self.relation_tree.change_ancestor(part_obj,parent_obj,obj_node.teleport_type)
            self.relation_tree.remove_ancestor(obj)
            self.teleport_relation(parent_obj)

        return True
    
    def clean_dust(self,obj):
        ## pre conditions
        in_cleaner=False
        if isinstance(obj,RoomFloor):
            obj=obj.floor_obj
        else:
            ## pre conditions
            try:
                self.check_interactability(obj)
            except ValueError as e:
                print(e)
                return False
            
            # check if obj is inside a toggled cleaner
            node=self.relation_tree.get_node(obj)
            allowed_cleaners=["dishwasher","sink"]
            while node.parent is not self.relation_tree.root:
                parent_obj=node.parent.obj
                if object_states.ToggledOn in parent_obj.states \
                and parent_obj.states[object_states.ToggledOn].get_value():
                    for allowed_cleaner in allowed_cleaners:
                        if allowed_cleaner in parent_obj.name:
                            in_cleaner=True
                            break
                if in_cleaner:
                    break
                node=node.parent
        
        
        if not (hasattr(obj, "states") and object_states.Dusty in obj.states):
            print("Clean-dust failed, object cannot be clean-dusted")
            return False
        
        if not obj.states[object_states.Dusty].get_value():
            print("Clean-dust failed, object is already clean-dusted")
            return False
        
        # check if cleaner in inventory
        has_cleaner=False
        for inventory_obj in self.robot_inventory.values():
            if inventory_obj is None:
                continue
            if hasattr(inventory_obj, "states") and object_states.CleaningTool in inventory_obj.states:
                has_cleaner=True
                break

        if not in_cleaner and not has_cleaner:
            print("Clean-dust failed, please place object in a toggled on cleaner or get a cleaner first")
            return False


        ## post effects
        self.navigate_to_if_needed(obj)
        obj.states[object_states.Dusty].set_value(False)
        print(f"Clean-dust {obj.name} success")
        return True
    
    def clean_stain(self,obj):
        ## pre conditions
        in_cleaner=False
        if isinstance(obj,RoomFloor):
            obj=obj.floor_obj
        else:
            try:
                self.check_interactability(obj)
            except ValueError as e:
                print(e)
                return False
            
            # check if obj is inside a toggled cleaner
            node=self.relation_tree.get_node(obj)
            allowed_clean_containers=["sink"]
            while node.parent is not self.relation_tree.root:
                parent_obj=node.parent.obj
                if object_states.ToggledOn in parent_obj.states \
                and parent_obj.states[object_states.ToggledOn].get_value():
                    for allowed_clean_container in allowed_clean_containers:
                        if allowed_clean_container in parent_obj.name:
                            in_cleaner=True
                            break
                if in_cleaner:
                    break
                node=node.parent
        
        if not (hasattr(obj, "states") and object_states.Stained in obj.states):
            print("Clean-stain, object cannot be clean-stained")
            return False
        
        if not obj.states[object_states.Stained].get_value():
            print("Clean-stain, object is already clean-stained")
            return False
        
        # check if has soaked cleaner in inventory
        has_soaked_cleaner=False
        allowed_cleaners=["detergent"]
        for inventory_obj in self.robot_inventory.values():
            if inventory_obj is None:
                continue

            if hasattr(inventory_obj, "states") and object_states.CleaningTool in inventory_obj.states \
            and object_states.Soaked in inventory_obj.states and inventory_obj.states[object_states.Soaked].get_value():
                has_soaked_cleaner=True
                break
                

            for allowed_cleaner in allowed_cleaners:
                if allowed_cleaner in inventory_obj.name:
                    has_soaked_cleaner=True
                    break

            
            if  has_soaked_cleaner:
                break

        if not in_cleaner and not has_soaked_cleaner:
            print("Clean-stain failed, please place object in a toggled on cleaner or get a soaked cleaner first")
            return False
        
        ## post effects
        self.navigate_to_if_needed(obj)
        obj.states[object_states.Stained].set_value(False)
        print(f"Clean-stain {obj.name} success")
        return True
    
    def soak_dry(self,obj,soak_or_dry:str):
        ## pre conditions
        try:
            self.check_interactability(obj)
        except ValueError as e:
            print(e)
            return False
        
        if not (hasattr(obj, "states") and object_states.Soaked in obj.states):
            print("Soak failed, object cannot be soaked")
            return False
        
        if obj.states[object_states.Soaked].get_value()==(soak_or_dry=='soak'):
            print(f"{soak_or_dry.capitalize()} failed, object is already {soak_or_dry}ed")
            return False
        
        # if soak_or_dry=='soak', obj must be put in a toggled sink
        allowed_soakers=["sink","teapot"]
        if soak_or_dry=='soak':
            in_sink=False
            node=self.relation_tree.get_node(obj)
            while node.parent is not self.relation_tree.root:
                parent_obj=node.parent.obj
                for allowed_soaker in allowed_soakers:
                    if allowed_soaker in parent_obj.name and (object_states.ToggledOn in parent_obj.states \
                    and parent_obj.states[object_states.ToggledOn].get_value() or \
                    object_states.ToggledOn not in parent_obj.states):
                        in_sink=True
                        break
                if in_sink:
                    break
                node=node.parent
            if not in_sink:
                print("Soak failed, please place object in a toggled on sink first")
                return False

        ## post effects
        self.navigate_to_if_needed(obj)
        obj.states[object_states.Soaked].set_value((soak_or_dry=='soak'))
        print(f"{soak_or_dry.capitalize()} {obj.name} success")
        return True
    
    def freeze_unfreeze(self,obj,freeze_or_unfreeze:str):
        assert freeze_or_unfreeze in ['freeze','unfreeze']
        ## pre conditions
        try:
            self.check_interactability(obj)
        except ValueError as e:
            print(e)
            return False
        
        if not (hasattr(obj, "states") and object_states.Frozen in obj.states):
            print("Freeze failed, object cannot be frozen")
            return False
        
        if obj.states[object_states.Frozen].get_value()==(freeze_or_unfreeze=='freeze'):
            print(f"{freeze_or_unfreeze.capitalize()} failed, object is already {freeze_or_unfreeze}ed")
            return False
        
        # has_freezer=False
        # for inventory_obj in self.inventory.values():
        #     if hasattr(inventory_obj, "states") and object_states.Freezer in inventory_obj.states:
        #         has_freezer=True
        #         break
        # if not has_freezer:
        #     print("Freeze failed, no freezer in inventory")
        #     return False
        
        ## post effects
        self.navigate_to_if_needed(obj)
        obj.states[object_states.Frozen].set_value((freeze_or_unfreeze=='freeze'))
        print(f"{freeze_or_unfreeze.capitalize()} {obj.name} success")
        return True
    
    def cook(self,obj):
        ## pre conditions
        try:
            self.check_interactability(obj)
        except ValueError as e:
            print(e)
            return False
        
        if not (hasattr(obj, "states") and object_states.Cooked in obj.states):
            print("Cook failed, object cannot be cooked")
            return False
        
        if obj.states[object_states.Cooked].get_value():
            print("Cook failed, object is already cooked")
            return False
        
        in_cooker=False
        allowered_cookers=["saucepan"]
        node=self.relation_tree.get_node(obj)
        while node.parent is not self.relation_tree.root:
            parent_obj=node.parent.obj
            for allowered_cooker in allowered_cookers:
                if allowered_cooker in parent_obj.name:
                    in_cooker=True
                    break
            if in_cooker:
                break
            node=node.parent
        if not in_cooker:
            print("Cook failed, please place object in a cooker first")
            return False
        
        ## post effects
        self.navigate_to_if_needed(obj)
        obj.states[object_states.Cooked].set_value(True)
        print(f"Cook {obj.name} success")
        return True
    ##################### for behavior task eval #####################
    def navigate(self,obj:URDFObject):
        return self.navigate_to(obj)
    
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
        # clean will clean both dust and stain
        flag1=False
        flag2=False
        try_clean_dust=False
        try_clean_stain=False
        if not (object_states.Dusty in obj.states and obj.states[object_states.Dusty].get_value()==False):
            flag1=self.clean_dust(obj)
            try_clean_dust=True
        if not (object_states.Stained in obj.states and obj.states[object_states.Stained].get_value()==False):
            flag2=self.clean_stain(obj)
            try_clean_stain=True
        if not (try_clean_dust or try_clean_stain):
            print("Clean failed, object is already clean")
            return False
        return flag1 or flag2

    
        



        

        
           



    
        