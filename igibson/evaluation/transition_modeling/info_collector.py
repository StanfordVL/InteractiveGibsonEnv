from igibson.evaluation.action_sequence.action_sequence_evaluator import ActionSequenceEvaluator
import os
import json
import fire
class InfoCollector(ActionSequenceEvaluator):
    def __init__(self, demo_dir,demo_name):
        self.demo_name=demo_name
        super(InfoCollector, self).__init__(demo_dir=demo_dir,demo_name=demo_name)
        self.info = []


    def get_initial_condition(self):
        return [cond.terms for cond in self.task.initial_conditions]
    
    def get_goal_condition(self):
        return [cond.terms for cond in self.task.goal_conditions]
    
    def get_goal_option(self):
        goal_combos=[]
        for goal_combo in self.task.ground_goal_state_options:
            goal_combos.append([head.terms for head in goal_combo])
        return goal_combos
    
    def get_name_category(self):
        name_mapping={}
        for name, obj in self.task.object_scope.items():
            category="_".join(name.split("_")[:-1])
            name_mapping[name]=category
        return name_mapping
    
    def save_info(self,save_dir):
        rst={}
        os.makedirs(save_dir,exist_ok=True)
        rst["initial_condition"]=self.get_initial_condition()
        rst["goal_condition"]=self.get_goal_condition()
        rst["goal_option"]=self.get_goal_option()
        rst["name_category"]=self.get_name_category()
        with open(os.path.join(save_dir,f"{self.demo_name}.json"),"w") as f:
            json.dump(rst,f,indent=4)

def main(demo_dir,demo_name_dir,save_dir):
    name_in_demo_dir=set()
    for demo in os.listdir(demo_dir):
        demo_name=demo.split(".")[0]
        name_in_demo_dir.add(demo_name)
    name_in_save_dir=set()
    for info in os.listdir(save_dir):
        name_in_save_dir.add(info.split(".")[0])
    for demo_name in os.listdir(demo_name_dir):
        demo_name=demo_name.split(".")[0]
        if demo_name not in name_in_demo_dir:
            continue
        if demo_name in name_in_save_dir:
            continue
        info_collector=InfoCollector(demo_dir,demo_name)
        info_collector.save_info(save_dir)
        print(f"Info for {demo_name} is saved")
if __name__=="__main__":
    fire.Fire(main)