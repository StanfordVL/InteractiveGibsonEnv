from igibson.evaluation.transition_modeling.transition_modeling_evaluator import TransitionModelingEvaluator
import os
import json
import fire
import random
from pddl.parser.problem import ProblemParser
from pddl.formatter import problem_to_string
import re
RANDOM_SEED = 0
NUM_GOALS = 4
random.seed(RANDOM_SEED)
class PDDLGenerator():
    def __init__(self, demo_dir,info_dir, demo_name):
        self.demo_name = demo_name
        self.info_dir = info_dir
        self.tme = TransitionModelingEvaluator(demo_dir=demo_dir, demo_name=demo_name)
        with open(os.path.join(self.info_dir, f"{self.demo_name}.json"), "r") as f:
            self.info = json.load(f)
        self.goal_option = self.info["goal_option"]
        self.name_category = self.info["name_category"]
        self.initial_condition= self.info["initial_condition"]

    def sample_goal(self,num_goals=NUM_GOALS):
        option_list=self.goal_option
        # randomly sample a option from the option list
        goal_option=random.choice(option_list)
        goals=[]
        # randomly sample num_goals goals from the option
        goals=random.sample(goal_option, min(num_goals, len(goal_option)))
        return goals
    
    def get_relevant_obj_for_goal(self, goals):
        goal_predicates = set()
        relevant_objects = set()
        for goal in goals:
            goal_predicates.add(self.get_predicate(goal))
            relevant_objects.update(self.get_objects(goal))
        predicate_obj_category_mapping={'dusty': ['vacuum.n.04', 'scrub_brush.n.01', 'piece_of_cloth.n.01', 'towel.n.01', 'rag.n.01', 'dishwasher.n.01', 'dishtowel.n.01', 'hand_towel.n.01'], 
                                        'stained': ['vacuum.n.04', 'scrub_brush.n.01', 'piece_of_cloth.n.01', 'towel.n.01', 'rag.n.01', 'dishwasher.n.01', 'dishtowel.n.01', 'hand_towel.n.01','sink.n.01'], 
                                        'soaked': ['teapot.n.01', 'sink.n.01'], 
                                        'sliced': ['carving_knife.n.01', 'countertop.n.01', 'knife.n.01'], 
                                        'frozen': ['electric_refrigerator.n.01'], 
                                        'cooked': ['pan.n.01']}
        for predicate in goal_predicates:
            if predicate in predicate_obj_category_mapping:
                for k,v in self.name_category.items():
                    if v in predicate_obj_category_mapping[predicate]:
                        relevant_objects.add(k)
        return relevant_objects
    
    def get_relevant_init_cond_and_obj(self,relevant_objects):
        cond_list=[]
        relevant_objects=set(relevant_objects)
        for cond in self.initial_condition:
            for obj in cond:
                if obj in relevant_objects:
                    cond_list.append(cond)
                    break
        for cond in cond_list:
            for obj in cond:
                if obj in self.name_category:
                    relevant_objects.add(obj)
        return {
            "objects": relevant_objects,
            "init_cond": cond_list
        }
    
    @staticmethod
    def convert_to_pddl_sentence(elements):
        if elements[0] == "not":
            # Wrap everything after "not" in parentheses
            inner_sentence = f"({' '.join(elements[1:])})"
            # Wrap the entire expression in parentheses
            pddl_sentence = f"(not {inner_sentence})"
        else:
            # Just join elements with space and wrap in parentheses
            pddl_sentence = f"({' '.join(elements)})"
        
        return pddl_sentence

    @staticmethod
    def get_predicate(elements):
        if elements[0] == "not":
            return elements[1]
        else:
            return elements[0]
        
    @staticmethod
    def get_objects(elements):
        if elements[0] == "not":
            return elements[2:]
        else:
            return elements[1:]

    

    def generate_pddl(self,template_path):
        with open(template_path, "r") as f:
            template = f.read()
        goals=self.sample_goal()
        relevant_objects=self.get_relevant_obj_for_goal(goals)
        relevant_all=self.get_relevant_init_cond_and_obj(relevant_objects)
        objects = relevant_all["objects"]
        init_cond = relevant_all["init_cond"]
        for obj in objects:
            init_cond.append(["same_obj", obj, obj])

        goal_str=""
        for goal in goals:
            goal_str+=self.convert_to_pddl_sentence(goal)+"\n"

        init_cond_str=""
        for cond in init_cond:
            init_cond_str+=self.convert_to_pddl_sentence(cond)+"\n"

        objects_str=""
        for obj in list(objects):
            if 'agent' in obj:
                continue
            objects_str+=f"{obj} - {self.name_category[obj]}\n"

        template=template.replace("<problem_name>",self.demo_name.split("_0_")[0])
        template=template.replace("<objects>",objects_str)
        template=template.replace("<init_cond>",init_cond_str)
        template=template.replace("<goal>",goal_str)
        template=template.replace(".",'_')

        problem = ProblemParser()(template)
        return problem_to_string(problem)


def get_problem_pddl(demo_dir, info_dir, demo_name):
    pddl_generator = PDDLGenerator(demo_dir, info_dir, demo_name)
    pddl=pddl_generator.generate_pddl(rb"D:\GitHub_jameskrw\iGibson\igibson\evaluation\transition_modeling\resources\pddl_template.txt")
    return pddl
def get_problem_pddl_batch(demo_dir, info_dir, name_dir,save_dir):
    pddl_files=[]
    os.makedirs(save_dir,exist_ok=True)
    name_in_demo_dir=set()
    for demo in os.listdir(demo_dir):
        demo_name=demo.split(".")[0]
        name_in_demo_dir.add(demo_name)
    name_in_save_dir=set()
    for info in os.listdir(save_dir):
        name_in_save_dir.add(info.split(".")[0])
    for demo_name in os.listdir(name_dir):
        demo_name=demo_name.split(".")[0]
        if demo_name not in name_in_demo_dir:
            continue
        if demo_name in name_in_save_dir:
            continue
        pddl= get_problem_pddl(demo_dir, info_dir, demo_name)
        with open(os.path.join(save_dir,f"{demo_name}.pddl"),"w") as f:
            f.write(pddl)
        pddl_files.append({
            "identifier": demo_name,
            "problem_file": pddl
        })
        print(f"PDDL for {demo_name} is saved")
    with open(os.path.join(save_dir,"pddl_files.json"),"w") as f:
        json.dump(pddl_files,f,indent=4)
if __name__ == "__main__":
    fire.Fire(get_problem_pddl_batch)

