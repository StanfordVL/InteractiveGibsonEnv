import igibson.object_states as object_states
from igibson.tasks.behavior_task import BehaviorTask
from igibson.utils.ig_logging import IGLogReader
from igibson.utils.utils import parse_config
import os
import igibson
from igibson.envs.igibson_env import iGibsonEnv
from tqdm import tqdm
import json



# Define the input and output paths
input_path = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/assets/100_selected_demos.txt"
output_path = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/assets/all_objects.json"
object_states_file = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/assets/object_states.json"


# retrieve relevant node and edge states from the object_states.json file
with open(object_states_file, 'r') as json_file:
    object_states = json.load(json_file)

relevant_node_states = object_states["node_states"]
relevant_edge_states = object_states["edge_states"]




class Env:
    def defalt_init(self,demo_path):
        task = IGLogReader.read_metadata_attr(demo_path, "/metadata/atus_activity")
        if task is None:
            task = IGLogReader.read_metadata_attr(demo_path, "/metadata/task_name")

        task_id = IGLogReader.read_metadata_attr(demo_path, "/metadata/activity_definition")
        if task_id is None:
            task_id = IGLogReader.read_metadata_attr(demo_path, "/metadata/task_instance")

        scene_id = IGLogReader.read_metadata_attr(demo_path, "/metadata/scene_id")

        config_filename = os.path.join(igibson.configs_path, "behavior_robot_mp_behavior_task.yaml")
        config = parse_config(config_filename)
        
        config["task"] = task
        config["task_id"] = task_id
        config["scene_id"] = scene_id
        config["robot"]["show_visual_head"] = True
        config["image_width"]=512
        config["image_height"]=512
        self.config = config
            
    def __init__(self,demo_path=None) -> None:
        self.config=None
        if demo_path is not None:
            self.defalt_init(demo_path)
            


def extract_substring(input_string):
    # Finding the last occurrence of '.' and '\''
    last_period_index = input_string.rfind('.')
    last_apostrophe_index = input_string.rfind("'")

    # Check if both characters are found in the string
    if last_period_index == -1 or last_apostrophe_index == -1:
        print("Either period or apostrophe not found in the string")
        raise

    # Extracting the substring between the last period and last apostrophe
    # Ensure that period comes before apostrophe for valid extraction
    if last_period_index < last_apostrophe_index:
        result = input_string[last_period_index + 1:last_apostrophe_index]
        return result
    else:
        print("Period occurs after the apostrophe, invalid for extraction.")
        raise


def get_objects(demo_path):
    
    objects = {}
    
    eenv=Env(demo_path=demo_path)
    igenv = iGibsonEnv(config_file=eenv.config)
    bt=BehaviorTask(igenv)
    
    for obj_name in bt.object_scope:
        obj_states = bt.object_scope[obj_name].states.keys()
        all_states = [extract_substring(str(state)) for state in obj_states]
        node_states = [state for state in all_states if state in relevant_node_states]
        
        print("obj_states:", obj_states)
        print("all_states:", all_states)
        print("node_states:", node_states)
        
        objects[obj_name] = node_states
    
    return objects  


def main():
    '''
    This script is used to generate relevant objects along with potential node states for the demos in the dataset.
    
    ----------------------------Required Inputs----------------------------
    input file containing demo names (input_path)
    input file containing allowed object states (object_states_file)
    
    ----------------------------Produced Outputs----------------------------
    output file containing relevant objects and node states for each demo (output_path)
    
    '''
    
    # Check if the output JSON file already exists and load existing data
    if os.path.exists(output_path):
        with open(output_path, 'r') as json_file:
            demo_to_objects = json.load(json_file)
    else:
        demo_to_objects = {}

    # Read demo names from the .txt file
    with open(input_path, 'r') as file:
        demo_names = file.read().splitlines()

    # Process each demo name with progress display using tqdm
    for demo_name in tqdm(demo_names):
        # Skip processing if demo_name is already in the JSON file
        if demo_name in demo_to_objects:
            continue

        # Create the full path for each demo
        demo_path = f"/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/data/virtual_reality/{demo_name}.hdf5"

        # Call the function to get the objects
        objects = get_objects(demo_path)

        # Add the result to the dictionary
        demo_to_objects[demo_name] = objects

        # Print the saved objects for transparency
        print("\n\n")
        print("Saving initial and goal conditions for demo: ", demo_name)
        print("objects: ", objects)
        print("\n\n")

        # Save the updated dictionary to the JSON file immediately
        with open(output_path, 'w') as json_file:
            json.dump(demo_to_objects, json_file, indent=4)

if __name__ == "__main__":
    main()
