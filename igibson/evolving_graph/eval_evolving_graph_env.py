from enum import IntEnum
from igibson.transition_model.base_env import BaseEnv
from igibson.envs.igibson_env import iGibsonEnv
from igibson.tasks.behavior_task import BehaviorTask
from igibson.objects.multi_object_wrappers import ObjectMultiplexer,ObjectGrouper
from igibson.objects.articulated_object import URDFObject
from igibson.robots import BaseRobot
import gym
from igibson.object_states.on_floor import RoomFloor
from enum import Enum, unique,auto
from .evolving_graph import EvolvingGraph
from copy import deepcopy


@unique
class EvalActions(IntEnum):
    NAVIGATE_TO=auto()
    LEFT_GRASP =auto()
    RIGHT_GRASP =auto()
    LEFT_PLACE_ONTOP =auto()
    RIGHT_PLACE_ONTOP =auto()
    LEFT_PLACE_INSIDE =auto()
    RIGHT_PLACE_INSIDE =auto()
    RIGHT_RELEASE =auto()
    LEFT_RELEASE =auto()
    OPEN =auto()
    CLOSE =auto()
    BURN =auto()
    COOK =auto()
    CLEAN =auto()
    FREEZE =auto()
    UNFREEZE =auto()
    SLICE =auto()
    SOAK =auto()
    DRY =auto()
    # STAIN =auto()
    TOGGLE_ON =auto()
    TOGGLE_OFF =auto()
    # UNCLEAN =auto()
    LEFT_PLACE_NEXTTO=auto()
    RIGHT_PLACE_NEXTTO=auto()
    LEFT_TRANSFER_CONTENTS_INSIDE=auto()
    RIGHT_TRANSFER_CONTENTS_INSIDE=auto()
    LEFT_TRANSFER_CONTENTS_ONTOP=auto()
    RIGHT_TRANSFER_CONTENTS_ONTOP=auto()

    LEFT_PLACE_NEXTTO_ONTOP=auto()
    RIGHT_PLACE_NEXTTO_ONTOP=auto()
    LEFT_PLACE_UNDER=auto()
    RIGHT_PLACE_UNDER=auto()

class EvalGraphEnv(BaseEnv):
    def __init__(self,config=None,demo_path=None,demo_dir=None,demo_name=None,task=None,**kwargs) -> None:
        assert config is not None or demo_path is not None or (demo_name is not None and demo_dir is not None) or task is not None
        if task is not None:
            self.task=task
        else:
            super().__init__(config,demo_path,demo_dir,demo_name,**kwargs)
            self.env = iGibsonEnv(config_file=self.config,**kwargs)
            self.task=self.env.task
        self.get_relevant_objects()
        self.action_env=EvolvingGraph(self.addressable_objects)
        self.control_function={
            EvalActions.LEFT_GRASP.value: self.action_env.left_grasp,
            EvalActions.RIGHT_GRASP.value: self.action_env.right_grasp,
            EvalActions.LEFT_PLACE_ONTOP.value: self.action_env.left_place_ontop,
            EvalActions.RIGHT_PLACE_ONTOP.value: self.action_env.right_place_ontop,
            EvalActions.LEFT_PLACE_NEXTTO.value: self.action_env.left_place_nextto,
            EvalActions.RIGHT_PLACE_NEXTTO.value: self.action_env.right_place_nextto,
            EvalActions.LEFT_PLACE_INSIDE.value: self.action_env.left_place_inside,
            EvalActions.RIGHT_PLACE_INSIDE.value: self.action_env.right_place_inside,
            EvalActions.RIGHT_RELEASE.value: self.action_env.right_release,
            EvalActions.LEFT_RELEASE.value: self.action_env.left_release,
            EvalActions.OPEN.value: self.action_env.open,
            EvalActions.CLOSE.value: self.action_env.close,
            EvalActions.CLEAN.value: self.action_env.clean,
            EvalActions.SLICE.value: self.action_env.slice,
            EvalActions.SOAK.value: self.action_env.soak,
            EvalActions.DRY.value: self.action_env.dry,
            EvalActions.FREEZE.value: self.action_env.freeze,
            EvalActions.UNFREEZE.value: self.action_env.unfreeze,
            EvalActions.LEFT_TRANSFER_CONTENTS_INSIDE.value: self.action_env.left_transfer_contents_inside,
            EvalActions.RIGHT_TRANSFER_CONTENTS_INSIDE.value: self.action_env.right_transfer_contents_inside,
            EvalActions.LEFT_TRANSFER_CONTENTS_ONTOP.value: self.action_env.left_transfer_contents_ontop,
            EvalActions.RIGHT_TRANSFER_CONTENTS_ONTOP.value: self.action_env.right_transfer_contents_ontop,
            EvalActions.TOGGLE_ON.value: self.action_env.toggle_on,
            EvalActions.TOGGLE_OFF.value: self.action_env.toggle_off,
            EvalActions.LEFT_PLACE_NEXTTO_ONTOP.value: self.action_env.left_place_nextto_ontop,
            EvalActions.RIGHT_PLACE_NEXTTO_ONTOP.value: self.action_env.right_place_nextto_ontop,
            EvalActions.LEFT_PLACE_UNDER.value: self.action_env.left_place_under,
            EvalActions.RIGHT_PLACE_UNDER.value: self.action_env.right_place_under,
            EvalActions.COOK.value: self.action_env.cook,
        }

    def get_relevant_objects(self):

        self.addressable_objects = set([
                item
                for item in self.task.object_scope.values()
                if isinstance(item, URDFObject) or isinstance(item, RoomFloor) or isinstance(item, ObjectMultiplexer)
            ])

        obj_in_multiplexer = set()
        #deal with multiplexed objects
        for obj in self.addressable_objects:
           if isinstance(obj, ObjectMultiplexer):
               for sub_obj in obj._multiplexed_objects:
                   if isinstance(sub_obj, URDFObject):
                        obj_in_multiplexer.add(sub_obj)
                   elif isinstance(sub_obj,ObjectGrouper):
                        for sub_sub_obj in sub_obj.objects:
                            if isinstance(sub_sub_obj, URDFObject):
                                obj_in_multiplexer.add(sub_sub_obj)
        self.addressable_objects.update(obj_in_multiplexer)
        self.addressable_objects = list(self.addressable_objects)
        # Filter out the robots and ObjectMultiplexer.
        self.addressable_objects = [obj for obj in self.addressable_objects if not isinstance(obj, BaseRobot) and not isinstance(obj, ObjectMultiplexer)]
        self.obj_name_to_obj = {obj.name: obj for obj in self.addressable_objects}
        self.obj_name_to_idx = {obj.name: idx for idx, obj in enumerate(self.addressable_objects)}

    def get_action_space(self):
        self.num_objects = len(self.addressable_objects)
        return gym.spaces.Tuple(
            [gym.spaces.Discrete(len(EvalActions)),gym.spaces.Discrete(len(self.addressable_objects))]
        )
    
    def apply_action(self,action,obj):
        cur_state=deepcopy(self.action_env.cur_state)
        if isinstance(action,str):
            action_idx=EvalActions[action].value
        obj_list=[self.obj_name_to_obj[obj_name.strip()] for obj_name in obj.strip().split(",")] 
        if len(obj_list)==1:
            flag=self.control_function[action_idx](obj_list[0])
        else:
            flag=self.control_function[action_idx](obj_list[0],obj_list[1])
        if flag:
            self.action_env.history_states.append(cur_state)
        return flag
