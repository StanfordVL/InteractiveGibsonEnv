from igibson.transition_model.base_env import BaseEnv
from igibson.envs.igibson_env import iGibsonEnv
from igibson.objects.multi_object_wrappers import ObjectMultiplexer,ObjectGrouper
from igibson.objects.articulated_object import URDFObject
from igibson.object_states.on_floor import RoomFloor
from igibson.evaluation.action_sequence.prompts.one_shot import prompt
from igibson.transition_model.eval_env import EvalEnv
from igibson.evolving_graph.eval_evolving_graph_env import EvalGraphEnv
from igibson.evolving_graph.eval_evolving_graph_env import EvalActions
import platform
from contextlib import redirect_stdout
import io
from collections import defaultdict
import traceback
BINARY_STATES=[
    'nextto',
    'ontop',
    'inside',
    'onfloor',
    'under',  
]

UNARY_STATES=[
    'cooked',
    'dusty',
    'frozen',
    'open',
    'sliced',
    'soaked',
    'stained',
    'toggled_on',
    'burnt',
]

ACTION_PARAMETER_LENGTH={
    "LEFT_PLACE_NEXTTO_ONTOP":2,
    "RIGHT_PLACE_NEXTTO_ONTOP":2,
}



class ActionSequenceEvaluator():
    def __init__(self, headless=True,**kwargs) -> None:
        self.transition_model=EvalEnv(mode="headless" if headless else "gui_non_interactive",
        use_pb_gui=(not headless and platform.system() != "Darwin"),**kwargs)
        self.task = self.transition_model.task
        self.evolving_graph=EvalGraphEnv(task=self.task,**kwargs)
        self.get_name_mapping()
        self.evaluation_info={
            "error_type":{
                "parsing":None,
                "hullucination":None,
                "arguments":None,
                "execution_success":True,
            },
            "goal_rst":{
                "all_goal_satisfied_ig":None,
                "all_goal_satisfied_graph":None,
                "tot_predicates":None,
                "tot_edge_predicates":None,
                "tot_node_predicates":None,
                "satisfied_predicates":None,
                "satisfied_edge_predicates":None,
                "satisfied_node_predicates":None,
                "pure_edge_predicates":None,
                "pure_node_predicates":None,
                "mixed_predicates":None,
                "satisfied_pure_edge_predicates":None,
                "satisfied_pure_node_predicates":None,
                "satisfied_mixed_predicates":None,

            },
            'initial_state':None,
            'target_state':None,
            'satisfication_info':None,
            'objects':None,
            "predicate_info":None,
            "execution_info":None,
            "parsed_actions":None,
        }
        self.object_name=set(self.evolving_graph.obj_name_to_obj.keys())
        self.action_name=set([action.name for action in EvalActions])
        

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
    
    
    def get_objects_str(self):
        objects=""
        for name in self.name_mapping.values():
            objects+=str(name)+"\n"
        return objects
    
    def get_prompt(self):
        return prompt.format(init_state=self.get_initial_state(),target_state=self.get_target_state(),obj_list=self.get_objects_str())

    # def get_raw_response(self,prompt):
    #     return call_gpt_with_retry(prompt)
    
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
        self.evaluation_info["parsed_actions"]=new_action
        return new_action
    
    def evaluate_format(self,actions):
        if len(actions)==0:
            self.evaluation_info["error_type"]["parsing"]="No actions found"
            return False
        for action in actions:
            if "action" not in action or "object" not in action:
                self.evaluation_info["error_type"]["parsing"]="action or object not found"
                return False
        for action in actions:
            action_name=action["action"]
            if action_name not in self.action_name:
                self.evaluation_info["error_type"]["hullucination"]=f"action {action_name} not found"
                return False
            for obj in action["object"].strip().split(","):
                obj_name=obj.strip()
                if obj_name not in self.object_name:
                    self.evaluation_info["error_type"]["hullucination"]=f"object {obj_name} not found"
                    return False
        for action in actions:
            len_arguments=len(action["object"].strip().split(","))
            action_name=action["action"]
            objects=action["object"]
            if len_arguments!=1 and len_arguments!=2:
                self.evaluation_info["error_type"]["arguments"]=f"wrong arguments: {objects}"
                return False
            if len_arguments==2 and action["action"] not in ACTION_PARAMETER_LENGTH:
                self.evaluation_info["error_type"]["arguments"]=f"wrong arguments: {objects} for action {action_name}"
                return False
            if len_arguments==1 and action["action"] in ACTION_PARAMETER_LENGTH:
                self.evaluation_info["error_type"]["arguments"]=f"wrong arguments: {objects} for action {action_name}"
                return False
        return True
    
    def get_goal_state(self):
        _,goal_status=self.task.check_success()

        edge_predicates=defaultdict(list)
        node_predicates=defaultdict(list)
        tot_edge_predicates=0
        tot_node_predicates=0
        satisfied_edge_predicates=0
        satisfied_node_predicates=0
        pure_edge_predicates=0
        pure_node_predicates=0
        satisfied_pure_edge_predicates=0
        satisfied_pure_node_predicates=0
        mixed_predicates=0
        satisfied_mixed_predicates=0
        for idx,goal_condition in enumerate(self.task.goal_conditions):
            flag_node=False
            flag_edge=False
            flag=True if idx in goal_status['satisfied'] else False
            for relation in BINARY_STATES:
                if relation in goal_condition.terms:
                    edge_predicates[relation].append(flag)
                    flag_edge=True
            for relation in UNARY_STATES:
                if relation in goal_condition.terms:
                    node_predicates[relation].append(flag)
                    flag_node=True
            tot_edge_predicates+=int(flag_edge)/(int(flag_edge)+int(flag_node)) if flag_edge or flag_node else 0
            tot_node_predicates+=int(flag_node)/(int(flag_edge)+int(flag_node)) if flag_edge or flag_node else 0
            if flag:
                satisfied_edge_predicates+=int(flag_edge)/(int(flag_edge)+int(flag_node)) if flag_edge or flag_node else 0
                satisfied_node_predicates+=int(flag_node)/(int(flag_edge)+int(flag_node)) if flag_edge or flag_node else 0
            if flag_edge and not flag_node:
                pure_edge_predicates+=1
                if flag:
                    satisfied_pure_edge_predicates+=1
            if flag_node and not flag_edge:
                pure_node_predicates+=1
                if flag:
                    satisfied_pure_node_predicates+=1
            if flag_edge and flag_node:
                mixed_predicates+=1
                if flag:
                    satisfied_mixed_predicates+=1

        predicate_info={}
        for k,v in edge_predicates.items():
            predicate_info[k]={
                'total':len(v),
                'satisfied':sum(v),
                'satisfied_rate':sum(v)/len(v) if len(v)>0 else 0
            }
        for k,v in node_predicates.items():
            predicate_info[k]={
                'total':len(v),
                'satisfied':sum(v),
                'satisfied_rate':sum(v)/len(v) if len(v)>0 else 0
            }
        goal_rst={
        'tot_goals': len(self.task.goal_conditions),
        'satisfied_goals': len(goal_status['satisfied']),
        'all_goal_satisfied_ig':len(goal_status['satisfied'])==len(self.task.goal_conditions),
        'tot_predicates':tot_edge_predicates+tot_node_predicates,
        'tot_edge_predicates': tot_edge_predicates,
        'tot_node_predicates': tot_node_predicates,
        'satisfied_edge_predicates': satisfied_edge_predicates,
        'satisfied_node_predicates': satisfied_node_predicates,
        "satisfied_predicates":satisfied_edge_predicates+satisfied_node_predicates,
        'predicate_info':predicate_info,
        "satisfication_info":goal_status,
        'pure_edge_predicates':pure_edge_predicates,
        'pure_node_predicates':pure_node_predicates,
        'mixed_predicates':mixed_predicates,
        'satisfied_pure_edge_predicates':satisfied_pure_edge_predicates,
        'satisfied_pure_node_predicates':satisfied_pure_node_predicates,
        'satisfied_mixed_predicates':satisfied_mixed_predicates,
        # 'execution_info':execution_info,
        }
        for k,v in self.evaluation_info.items():
            if isinstance(v,dict):
                for kk,vv in v.items():
                    if kk in goal_rst:
                        self.evaluation_info[k][kk]=goal_rst[kk]        
            elif k in goal_rst:
                self.evaluation_info[k]=goal_rst[k]
        return goal_rst


    def evaluate_goal(self,actions,ending_step=None):
        for idx,action in enumerate(actions):
            if ending_step is not None and idx>ending_step:
                break
            try:
                action_name=action["action"]
                obj=action["object"]
                flag=self.transition_model.apply_action(action_name,obj)
            except Exception as e:
                msg=traceback.format_exc()
                
        if not self.task.check_success()[0]:
            self.transition_model.final_step()
        return self.get_goal_state()
    

    def evaluate_trajectory(self,actions):
        execution_info=[]
        for idx,action in enumerate(actions):
            rst={}
            flag=True
            try:
                action_name=action["action"]
                obj=action["object"]
                rst["action"]=action_name
                rst['object']=obj
                f=io.StringIO()
                with redirect_stdout(f):
                    flag=self.evolving_graph.apply_action(action_name,obj)
                rst_str=f.getvalue()
                rst['execution_success']=flag
                if not flag:
                    errors=self.evaluate_trajectory_parse_error(rst_str)
                    rst.update(errors)
                    error_dict={error['error_type']:error['error_reason'] for error in errors["errors"]}
                    if "ErrorType.ADDITIONAL_STEP" in error_dict:
                        self.evaluation_info["error_type"]["ErrorType.ADDITIONAL_STEP"]=error_dict["ErrorType.ADDITIONAL_STEP"]
                        flag=True
                    elif "ErrorType.AFFORDANCE_ERROR" in error_dict:
                        self.evaluation_info["error_type"]["ErrorType.AFFORDANCE_ERROR"]=error_dict["ErrorType.AFFORDANCE_ERROR"]
                    elif "ErrorType.WRONG_TEMPORAL_ORDER" in error_dict:
                        self.evaluation_info["error_type"]["ErrorType.WRONG_TEMPORAL_ORDER"]=error_dict["ErrorType.WRONG_TEMPORAL_ORDER"]
                    elif "ErrorType.MISSING_STEP" in error_dict:
                        self.evaluation_info["error_type"]["ErrorType.MISSING_STEP"]=error_dict["ErrorType.MISSING_STEP"]
            except Exception as e:
                msg=traceback.format_exc()
                rst["errors"]=[{
                    "error_type":"unknown_execution_error",
                    "error_reason":str(e)+msg
                }]
                flag=False
                rst["execution_success"]=flag
                self.evaluation_info["unknown_execution_error"]=str(e)+msg
            rst['step']=idx
            execution_info.append(rst)
            if not flag:
                self.evaluation_info["error_type"]["execution_success"]=False
                break
            
        all_action_executable=self.evaluation_info["error_type"]["execution_success"]
        goal_rst={
            'tot_steps':len(actions),
            'tot_executable_steps':len(execution_info) if all_action_executable else len(execution_info)-1,
            'all_goal_satisfied_graph':self.evolving_graph.action_env.cur_state.check_success(self.task)["success"],
            'execution_info':execution_info
        }
        for k,v in self.evaluation_info.items():
            if isinstance(v,dict):
                for kk,vv in v.items():
                    if kk in goal_rst:
                        self.evaluation_info[k][kk]=goal_rst[kk]        
            elif k in goal_rst:
                self.evaluation_info[k]=goal_rst[k]
        return goal_rst
            
    def evaluate_trajectory_parse_error(self,rst_str):
        lines=rst_str.strip().split("\n")
        errors=[]
        for line in lines:
            if "<Error>" in line:
                error_reason=line.split('<Reason>')[1].strip()
                error_type=line.split('<Error>')[1].split('<Reason>')[0].strip()
                errors.append({
                    "error_type":error_type,
                    "error_reason":error_reason
                })
        return {"errors":errors}
    
    def evaluate_parsed(self,actions):
        self.evaluation_info['initial_state']=self.get_initial_state().strip().split("\n")
        self.evaluation_info['target_state']=self.get_target_state().strip().split("\n")
        self.evaluation_info['objects']=self.name_mapping
        tr_rst=self.evaluate_trajectory(actions)
        ig_rst=self.evaluate_goal(actions,ending_step=tr_rst['tot_executable_steps']-1)
        return self.evaluation_info
    
    def evaluate_all(self,response):
        self.evaluation_info['initial_state']=self.get_initial_state().strip().split("\n")
        self.evaluation_info['target_state']=self.get_target_state().strip().split("\n")
        self.evaluation_info['objects']=self.name_mapping
        actions=self.parse_response(response)
        if not self.evaluate_format(actions):
            self.get_goal_state()
            self.evaluation_info["error_type"]["execution_success"]=False
            return self.evaluation_info
        tr_rst=self.evaluate_trajectory(actions)
        
        ig_rst=self.evaluate_goal(actions,ending_step=tr_rst['tot_executable_steps']-1)
        return self.evaluation_info

    


    

