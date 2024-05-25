from igibson.transition_model.base_env import BaseEnv
from igibson.envs.igibson_env import iGibsonEnv
from igibson.objects.multi_object_wrappers import ObjectMultiplexer,ObjectGrouper
from igibson.objects.articulated_object import URDFObject
from igibson.object_states.on_floor import RoomFloor
from igibson.evaluation.action_sequence.prompts.one_shot import prompt
from igibson.evaluation.utils.gpt_utils import call_gpt_with_retry
from igibson.transition_model.eval_env import EvalEnv
from igibson.evolving_graph.eval_evolving_graph_env import EvalGraphEnv
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
                "output_parsable":None,
                "parameter_error":None,
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
            },
            'initial_state':None,
            'target_state':None,
            'satisfication_info':None,
            'objects':None,
            "predicate_info":None,
            "execution_info":None,
        }
        

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
    
    def evaluate_format(self,actions):
        if len(actions)==0:
            self.evaluation_info["error_type"]["output_parsable"]="No actions found"
            return False
        for action in actions:
            if "action" not in action or "object" not in action:
                self.evaluation_info["error_type"]["output_parsable"]="action or object not found"
                return False
            parameter_length=len(action["object"].strip().split(","))
            if parameter_length>1:
                action_name=action["action"].strip()
                if action_name not in ACTION_PARAMETER_LENGTH:
                    self.evaluation_info["error_type"]["parameter_correct"]=f"{action_name} only support 1 parameter"
                    return False
        return True
    
    def get_goal_state(self):
        _,goal_status=self.task.check_success()

        edge_predicates=defaultdict(list)
        node_predicates=defaultdict(list)
        for idx,goal_condition in enumerate(self.task.goal_conditions):
            flag=True if idx in goal_status['satisfied'] else False
            for relation in BINARY_STATES:
                if relation in goal_condition.terms:
                    edge_predicates[relation].append(flag)
            for relation in UNARY_STATES:
                if relation in goal_condition.terms:
                    node_predicates[relation].append(flag)

        tot_edge_predicates=sum([len(v) for v in edge_predicates.values()])
        tot_node_predicates=sum([len(v) for v in node_predicates.values()])
        tot_edge_predicates_satisfied=sum([sum(v) for v in edge_predicates.values()])
        tot_node_predicates_satisfied=sum([sum(v) for v in node_predicates.values()])

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
        'satisfied_edge_predicates': tot_edge_predicates_satisfied,
        'satisfied_node_predicates': tot_node_predicates_satisfied,
        "satisfied_predicates":tot_edge_predicates_satisfied+tot_node_predicates_satisfied,
        'edge_predicates_succ_rate': tot_edge_predicates_satisfied/tot_edge_predicates if tot_edge_predicates>0 else 0,
        'node_predicates_succ_rate': tot_node_predicates_satisfied/tot_node_predicates if tot_node_predicates>0 else 0,
        'tot_predicates_succ_rate': (tot_edge_predicates_satisfied+tot_node_predicates_satisfied)/(tot_edge_predicates+tot_node_predicates) if (tot_edge_predicates+tot_node_predicates)>0 else 0,
        'tot_goal_succ_rate': len(goal_status['satisfied'])/len(self.task.goal_conditions) if len(self.task.goal_conditions)>0 else 0,
        'node_predicates':node_predicates,
        'edge_predicates':edge_predicates,
        'predicate_info':predicate_info,
        "satisfication_info":goal_status,
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

        execution_info=[]
        for idx,action in enumerate(actions):
            if ending_step is not None and idx>ending_step:
                break
            rst={}
            try:
                action_name=action["action"]
                obj=action["object"]
                rst["action"]=action_name
                rst['object']=obj
                flag=self.transition_model.apply_action(action_name,obj)
                rst['execution_success']=flag
            except Exception as e:
                msg=traceback.format_exc()
                rst["unknown_execution_error"]=str(e)+msg
                rst["execution_success"]=False
            rst['step']=idx
            rst['current_goal_condition']=self.task.check_success()
            execution_info.append(rst)

        if not self.task.check_success()[0]:
            self.transition_model.final_step()
            rst={
                'action':"teleport_all",
                'step':len(actions),
                'current_goal_condition':self.task.check_success(),
            }

        execution_info.append(rst)
        return self.get_goal_state()
    

    def evaluate_trajectory(self,actions):
        execution_info=[]
        for idx,action in enumerate(actions):
            rst={}
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
                    for error in errors["errors"]:
                        self.evaluation_info["error_type"][error['error_type']]=error['error_reason']
                    rst.update(errors)
            except Exception as e:
                msg=traceback.format_exc()
                rst["errors"]=[{
                    "error_type":"name_hullucination",
                    "error_reason":str(e)+msg
                }]
                flag=False
                rst["execution_success"]=flag
                self.evaluation_info["name_hullucination"]=str(e)+msg
            rst['step']=idx
            execution_info.append(rst)
            self.evaluation_info
            if not flag:
                break

        goal_rst={
            'tot_steps':len(actions),
            'tot_executed_steps':len(execution_info),
            'all_goal_satisfied_graph':self.evolving_graph.action_env.cur_state.check_success(self.task),
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
        ig_rst=self.evaluate_goal(actions,ending_step=tr_rst['tot_executed_steps']+1)
        return self.evaluation_info
    
    def evaluate_all(self,response):
        self.evaluation_info['initial_state']=self.get_initial_state().strip().split("\n")
        self.evaluation_info['target_state']=self.get_target_state().strip().split("\n")
        self.evaluation_info['objects']=self.name_mapping
        actions=self.parse_response(response)
        if not self.evaluate_format(actions):
            self.get_goal_state()
            return self.evaluation_info
        tr_rst=self.evaluate_trajectory(actions)
        ig_rst=self.evaluate_goal(actions,ending_step=tr_rst['tot_executed_steps']+1)
        return self.evaluation_info

    


    

