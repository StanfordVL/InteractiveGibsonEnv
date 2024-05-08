from igibson.transition_model.base_env import BaseEnv
from igibson.envs.igibson_env import iGibsonEnv
from igibson.objects.multi_object_wrappers import ObjectMultiplexer,ObjectGrouper
from igibson.objects.articulated_object import URDFObject
from igibson.object_states.on_floor import RoomFloor
from igibson.evaluation.action_sequence.prompts.zero_shot import zero_shot
from igibson.evaluation.utils.gpt_utils import call_gpt_with_retry

class ActionSequenceEvaluator(BaseEnv):
    def __init__(self, config=None,demo_path=None,**kwargs) -> None:
        super().__init__(config,demo_path,**kwargs)
        self.env = iGibsonEnv(config_file=self.config,**kwargs)
        self.task = self.env.task
        self.get_name_mapping()

    def get_name_mapping(self):
        self.name_mapping={}
        for name, obj in self.task.object_scope.items():
            category="_".join(name.split("_")[:-1])
            if isinstance(obj, ObjectMultiplexer):
                self.name_mapping[name]={"name":obj.name.rstrip("_multiplexer"),"category":category}
            elif isinstance(obj, RoomFloor) or isinstance(obj, URDFObject):
                self.name_mapping[name]={"name":obj.name,"category":category}


    def get_initial_state(self):
        initial_state=""
        for goal_cond in self.task.initial_conditions:
            a=goal_cond.terms
            b=[]
            for name in a:
                if name in self.name_mapping:
                    b.append(self.name_mapping[name]["name"])
                else:
                    b.append(name)
            initial_state+=str(b)+"\n"
        return initial_state
    
    def get_target_state(self):
        target_state=""
        for goal_cond in self.task.goal_conditions:
            a=goal_cond.terms
            b=[]
            for name in a:
                if name in self.name_mapping:
                    b.append(self.name_mapping[name]["name"])
                else:
                    b.append(name)
            target_state+=str(b)+"\n"
        return target_state
    
    def get_objects(self):
        objects=""
        for name in self.name_mapping.values():
            objects+=str(name)+"\n"
        return objects
    
    def get_prompt_zeroshot(self):
        return zero_shot.format(init_state=self.get_initial_state(),target_state=self.get_target_state(),obj_list=self.get_objects())

    def get_raw_response(self,prompt):
        return call_gpt_with_retry(prompt)
    
    def parse_response(self,response):
        # find [ and ]
        try:
            start_idx=response.find("[")
            end_idx=response.find("]")
            action_list=eval(response[start_idx:end_idx+1])
            new_action=[]
            for action in action_list:
                if isinstance(action,dict):
                    if "action" in action and "object" in action:
                        new_action.append(action)
        except Exception as e:
            print(e)
            new_action=[]
        return new_action
    

