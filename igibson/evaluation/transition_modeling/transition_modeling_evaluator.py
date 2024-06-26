from igibson.transition_model.base_env import BaseEnv
from igibson.envs.igibson_env import iGibsonEnv
from igibson.objects.multi_object_wrappers import ObjectMultiplexer,ObjectGrouper
from igibson.objects.articulated_object import URDFObject
from igibson.object_states.on_floor import RoomFloor
from igibson.evaluation.transition_modeling.prompts.prompts import prompt2 as prompt
from bddl.config import get_definition_filename
import os
import json
import re
from igibson.evaluation.transition_modeling.logic_score import calculate_logic_score
DOMAIN_FILE_PATH = "igibson/evaluation/transition_modeling/data/resources/behavior_new.pddl"
HUMAN_ANNOTATION_PATH="igibson/evaluation/data/action_sequence_human_annotations"
GT_DATA_PATH="igibson/evaluation/transition_modeling/data/resources/problem_pddl.json"

with open(GT_DATA_PATH) as f:
    GT_DATA=json.load(f)

ACTION_HANDLER_MAPPING={
    "NAVIGATE_TO":"navigate_to",
    "LEFT_GRASP":"grasp",
    "RIGHT_GRASP":"grasp",
    "LEFT_PLACE_ONTOP":"place_ontop",
    "RIGHT_PLACE_ONTOP":"place_ontop",
    "LEFT_PLACE_INSIDE":"place_inside",
    "RIGHT_PLACE_INSIDE":"place_inside",
    "OPEN":"open",
    "CLOSE":"close",
    "COOK":"cook",
    "FREEZE":"freeze",
    "SLICE":"slice",
    "SOAK":"soak",
    "TOGGLE_ON":"toggle_on",
    "LEFT_PLACE_NEXTTO":"place_nextto",
    "RIGHT_PLACE_NEXTTO":"place_nextto",
    "LEFT_PLACE_UNDER":"place_under",
    "RIGHT_PLACE_UNDER":"place_under",
    "LEFT_PLACE_NEXTTO_ONTOP":"place_nextto_ontop",
    "RIGHT_PLACE_NEXTTO_ONTOP":"place_nextto_ontop",
}

class TransitionModelingEvaluator(BaseEnv):
    def __init__(self, demo_dir,demo_name,domain_file_path=DOMAIN_FILE_PATH,human_annotation_path=HUMAN_ANNOTATION_PATH) -> None:
        super().__init__(demo_dir=demo_dir,demo_name=demo_name)
        self.demo_name=demo_name
        self.domain_file_path=domain_file_path
        self.human_attotation_path=human_annotation_path
        self.problem_pddl=self.get_problem_pddl()
        self.domain_pddl=self.get_domain_pddl()
        self.gold_actions=self.extract_action_details(content=self.domain_pddl)


    def get_action_handler(self,gt_data=GT_DATA):
        action_handler=set()
        for action in gt_data[self.demo_name]['actions']:
            action_handler.add(action.split(" ")[0].strip())
        return list(action_handler)   
                        
    def get_llm_input_action_handler(self)->str:
        action_str=""
        action_handler=self.get_action_handler()
        for action in action_handler:
            action_str+=f"(:action {action})\n"
            action_str+=f":parameters {self.gold_actions[action]['action_parameters']}\n"
            action_str+=f":precondition ()\n"
            action_str+=f":effect ()\n"
            action_str+=")\n"
        return action_str
       

    def get_domain_pddl(self):
        with open(self.domain_file_path) as f:
            domain_pddl=f.read()
        return domain_pddl
    
    @staticmethod
    # copied from https://github.com/zsyJosh/AgentEval/blob/shiyu_dev/virtualhome/simulation/evolving_graph/eval_robots.py
    # Author: Shiyu Zhao 
    def extract_action_details(domain_file_path='', content=None):
        if content is None:
            with open(domain_file_path, 'r') as file:
                content = file.read()
        content = re.sub(r';.*$', '', content, flags=re.MULTILINE)
        content = ' '.join(content.split())
        def extract_block(content, start_idx):
            open_paren = 1
            i = start_idx
            if content[i] == ')':
                return ')'
            while open_paren > 0:
                i += 1
                if content[i] == '(':
                    open_paren += 1
                elif content[i] == ')':
                    open_paren -= 1
            return content[start_idx:i+1]
        actions = {}
        action_pattern = re.compile(r'\(:action\s+(\w+)')
        idx = 0
        while True:
            action_match = action_pattern.search(content, idx)
            if not action_match:
                break
            action_name = action_match.group(1)
            start = action_match.end()
            # Locate the indices for parameters, precondition, and effect
            param_idx = content.find(':parameters', start)
            precon_idx = content.find(':precondition', start)
            effect_idx = content.find(':effect', start)
            if param_idx == -1 or precon_idx == -1 or effect_idx == -1:
                break
            # Extract the blocks based on balanced parentheses
            params = extract_block(content, content.find('(', param_idx) + 1)
            preconds = extract_block(content, content.find('(', precon_idx) + 1)
            effects = extract_block(content, content.find('(', effect_idx) + 1)
            # Clean text and add to the actions dictionary
            action_param = '(' + ' '.join(params.split())
            action_precond = '(' + ' '.join(preconds.split())
            action_effects = '(' + ' '.join(effects.split())
            action_param = action_param.replace(') )', '))')
            action_precond = action_precond.replace(') )', '))')
            action_effects = action_effects.replace(') )', '))')
            actions[action_name] = {
                'action_name': action_name,
                'action_parameters': action_param,
                'action_preconditions': action_precond,
                'action_effects': action_effects
            }
            # Update the search index to continue past this action
            idx = effects.find(')') + effect_idx + 1
        return actions

    
    def get_problem_pddl(self)->str:
        behavior_activity=self.config.get("task")
        instance=self.config.get("task_id")
        file_name=get_definition_filename(behavior_activity,instance)
        with open(file_name) as f:
            problem_pddl=f.read()
        return problem_pddl
    
    def get_modified_pddl(self,gt_data=GT_DATA)->str:
        return gt_data[self.demo_name]['problem_pddl']
    
    def get_prompt(self,gt_data=GT_DATA):
        return prompt.format(problem_file=self.get_modified_pddl(gt_data),action_handler=self.get_llm_input_action_handler())
    
    def parse_response(self,response):
        parsed_actions=self.extract_action_details(content=response)
        self.llm_actions=parsed_actions
        return parsed_actions


    def compute_score(self,parsed_response:dict):   
        action_precond = 0.0
        action_effect = 0.0
        score_dict={}
        for action_name, action_dict in parsed_response.items():
            pred_str = ''
            body_str = ''
            gold_str = ''
            gold_body_str = ''
            pred_str += f':action {action_name}\n'
            pred_str += f'  :parameters {action_dict["action_parameters"]}\n'
            pred_str += f'  :preconditions {action_dict["action_preconditions"]}\n'
            body_str += f'  :preconditions {action_dict["action_preconditions"]}\n'
            pred_str += f'  :effects {action_dict["action_effects"]}\n'
            body_str += f'  :effects {action_dict["action_effects"]}\n'
            
            try:
                gold_action = self.gold_actions[action_name]
            except:
                gold_action = {"action_name": f"{action_name}","action_parameters": "()", "action_preconditions": "()", "action_effects": "()"}
            gold_str += f':action {action_name}\n'
            gold_str += f'  :parameters {gold_action["action_parameters"]}\n'
            gold_str += f'  :preconditions {gold_action["action_preconditions"]}\n'
            gold_body_str += f'  :preconditions {gold_action["action_preconditions"]}\n'
            gold_str += f'  :effects {gold_action["action_effects"]}\n'
            gold_body_str += f'  :effects {gold_action["action_effects"]}\n'
            # act_similarity_score =  SequenceMatcher(None, body_str, gold_body_str).ratio()
            precond_similarity_score = calculate_logic_score(action_dict["action_preconditions"], gold_action["action_preconditions"])
            effect_similarity_score = calculate_logic_score(action_dict['action_effects'], gold_action['action_effects'])
            action_precond += precond_similarity_score
            action_effect += effect_similarity_score
            print(f'action {action_name} precondition score = {precond_similarity_score}')
            print(f'action {action_name} effect score = {effect_similarity_score}')
            score_dict[action_name] = {"precondition_score": precond_similarity_score, "effect_score": effect_similarity_score}
        
        
        action_precond = action_precond / len(parsed_response)  if len(parsed_response) > 0 else 0.0
        action_effect = action_effect / len(parsed_response) if len(parsed_response) > 0 else 0.0
        score_dict["avg_summary"] = {"precondition_score": action_precond, "effect_score": action_effect}
        return score_dict
    

