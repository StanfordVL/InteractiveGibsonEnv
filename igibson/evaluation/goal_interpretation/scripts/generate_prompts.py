from tqdm import tqdm
import json


# define the prompt save path
prompt_save_path = "./igibson/evaluation/goal_interpretation/data/goal_interpretation_prompts.json"



# Fixed paths (you should not have to change these paths)
demo_to_conds_path = "./igibson/evaluation/goal_interpretation/data/all_conditions.json"
demo_to_objs_path = "./igibson/evaluation/goal_interpretation/data/all_objects.json"
task_to_instructions_path = "./igibson/evaluation/goal_interpretation/data/instructions_by_activity_name.json"
prompt_path = "./igibson/evaluation/goal_interpretation/prompts/behavior_goal_interpretation.txt"
task_to_demo_path = "./igibson/evaluation/goal_interpretation/data/task_to_demo.json"




def main():
    '''
    This script is used to generate GPT prompts for goal conditions for the demos in the dataset.
    
    ----------------------------Required Inputs----------------------------
    base prompt to be modified (prompt_path)
    relevant objects (with all possible states) (demo_to_objs_path)
    initial and goal conditions (demo_to_conds_path)
    task instructions (task_to_instructions_path)
    list of demo names (demo_names_path)
    mapping from task name to demo name (task_to_demo_path)
    -----------------------------------------------------------------------
    
    ----------------------------Produced Outputs----------------------------
    all final generated prompts (prompt_save_path)
    ------------------------------------------------------------------------
    
    '''
    with open(demo_to_conds_path, 'r') as json_file:
        demo_to_conds = json.load(json_file)

    with open(demo_to_objs_path, 'r') as json_file:
        demo_to_objs = json.load(json_file)

    with open(task_to_instructions_path, 'r') as json_file:
        task_to_instructions = json.load(json_file)
        
    with open(task_to_demo_path, 'r') as json_file:
        task_to_demos = json.load(json_file)




    demo_to_llm_prompts = {}
    
    
    
    for key, value in tqdm(task_to_demos.items()):
        task_name = key
        demo_name = value
        


        initial_conditions = demo_to_conds[demo_name]["initial_conditions"]
        objects = demo_to_objs[demo_name]
        instructions = task_to_instructions[task_name]
        
        initial_conditions_string = '\n'.join(str(lst) for lst in initial_conditions.values())
        objects_string = '\n'.join(f"{key}: {value}" for key, value in objects.items())
        instructions_string = json.dumps({"Task Name": task_name, "Goal Instructions": instructions}, indent=4)
        
        generic_prompt = open(prompt_path, 'r').read()
        
        prompt = generic_prompt.replace('<object_in_scene>', objects_string)
        prompt = prompt.replace('<all_initial_states>', initial_conditions_string)
        prompt = prompt.replace('<instructions_str>', instructions_string)
        
        # save the prompts as well
        demo_to_llm_prompts[demo_name] = prompt
        
        
        
    # save the prompts
    with open(prompt_save_path, 'w') as json_file:
        json.dump(demo_to_llm_prompts, json_file, indent=4)
    
    print("prompts saved to: ", prompt_save_path)
    

if __name__ == "__main__":
    main()