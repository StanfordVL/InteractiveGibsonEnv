import igibson.object_states as object_states
from igibson.tasks.behavior_task import BehaviorTask
from igibson.utils.ig_logging import IGLogReader
from igibson.utils.utils import parse_config
import os
import igibson
from igibson.envs.igibson_env import iGibsonEnv
from igibson.transition_model_v3.eval_env import EvalEnv
from igibson.transition_model_v3.eval_env import EvalActions
from tqdm import tqdm
import json


demo_to_conds_path = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/assets/all_conditions.json"
demo_to_objs_path = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/assets/all_objects.json"
demo_names_path = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/assets/100_selected_demos.txt"
task_to_instructions_path = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/assets/instructions_by_activity_name_v2.json"
prompt_path = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/prompts/behavior_goal_interpretation.txt"
task_to_demo_path = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/assets/task_to_demo.json"
demo_to_prompt_path = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/assets/llm_prompts_v2.json"


with open(demo_to_conds_path, 'r') as json_file:
    demo_to_conds = json.load(json_file)

with open(demo_to_objs_path, 'r') as json_file:
    demo_to_objs = json.load(json_file)

with open(demo_to_prompt_path, 'r') as json_file:
    demo_to_prompt = json.load(json_file)

with open(task_to_instructions_path, 'r') as json_file:
    task_to_instructions = json.load(json_file)
    
with open(task_to_demo_path, 'r') as json_file:
    task_to_demos = json.load(json_file)

with open(demo_names_path, 'r') as file:
    demo_names = file.read().splitlines()
    
    

object_states = {
    "node_states": [
        "Cooked",
        "Dusty",
        "Frozen",
        "Open",  
        "Sliced",
        "Soaked",
        "Stained",
        "Toggled_On"
    ],
    "edge_states": [
        "Inside",
        "NextTo",
        "OnFloor",
        "OnTop",
        "Touching",
        "Under"
    ]
}



def is_node_condition(condition):
    """check of a condition is a node condition."""
    
    # first check based on the state
    try:
        for state in object_states["node_states"]:
            if is_state_condition(state, condition):
                return True
    # if that does not work, check based on the length of the condition
    except:
        if condition[0] == "not":
            if len(condition[1]) == 2:
                return True
        else:
            if len(condition) == 2:
                return True
    return False
            
def is_edge_condition(condition):
    """check of a condition is an edge condition."""
    
    # first check based on the state
    try:
        for state in object_states["edge_states"]:
            if is_state_condition(state, condition):
                return True
                     
    # if that does not work, check based on the length of the condition
    except:
        if condition[0] == "not":
            if len(condition[1]) == 3:
                return True
        else:
            if len(condition) == 3:
                return True
    return False
    

def is_state_condition(state, condition):
    """check if the given condition is about the given state."""
    if condition[0] == 'not':
        return condition[1][0] == state.lower()
    else:
        return condition[0] == state.lower()
    

def compute_metrics_by_state(all_satisfied_conditions, all_unsatisfied_conditions, predicted_conditions):
    """Compute metrics for each state separately."""
    node_state_results = {}
    edge_state_results = {}
    
    for state in object_states["node_states"]:
        node_state_results[state] = compute_metrics(
            [condition for condition in all_satisfied_conditions if is_state_condition(state, condition)],
            [condition for condition in all_unsatisfied_conditions if is_state_condition(state, condition)],
            [condition for condition in predicted_conditions if is_state_condition(state, condition)],
            keep_conditions=False
        )
    
    for state in object_states["edge_states"]:
        edge_state_results[state] = compute_metrics(
            [condition for condition in all_satisfied_conditions if is_state_condition(state, condition)],
            [condition for condition in all_unsatisfied_conditions if is_state_condition(state, condition)],
            [condition for condition in predicted_conditions if is_state_condition(state, condition)],
            keep_conditions=False
        )
    
    return node_state_results, edge_state_results
            


# Grammatical Error Checks

def is_of_correct_length(condition):
    """check if a condition is of correct length."""
    if condition[0] == "not":
        if len(condition[1]) == 2 or len(condition[1]) == 3:
            return True
    else:
        if len(condition) == 2 or len(condition) == 3:
            return True
    # if the condition length is neither 2 nor 3, return False
    return False

def contains_valid_state(condition):
    """check if a condition contains valid state."""
    for state in object_states["node_states"]:
        if is_state_condition(state, condition):
            return True
    for state in object_states["edge_states"]:
        if is_state_condition(state, condition):
            return True
    # if the state is neither a valid node state nor a valid edge state, return False
    return False

def contains_valid_objects(condition, demo):
    """check if a conditions contains valid objects from the demo"""
    legal_objects = list(demo_to_objs[demo].keys())
    used_objects = []
    if condition[0] == "not":
        if len(condition[1]) == 2:
            used_objects.append(condition[1][1])
        elif len(condition[1]) == 3:
            used_objects.append(condition[1][1])
            used_objects.append(condition[1][2])
        else:
            assert not is_of_correct_length(condition)
            pass
    else:
        if len(condition) == 2:
            used_objects.append(condition[1])
        elif len(condition) == 3:
            used_objects.append(condition[1])
            used_objects.append(condition[2])
    
    for obj in used_objects:
        if obj not in legal_objects:
            return False
    return True



def dataset_error_analysis(all_satisfied_conditions: list, all_unsatisfied_conditions: list, all_false_positive_conditions: list, predicted_conditions: list, num_object_hallucinations: int):
    """Compute metrics for node and edge conditions separately."""
    
    grammatically_valid_predicted_conditions = []
    wrong_length = []
    state_hallucination = []
    for condition in predicted_conditions:
        if contains_valid_state(condition) and is_of_correct_length(condition):
            grammatically_valid_predicted_conditions.append(condition)
        if not is_of_correct_length(condition):
            wrong_length.append(condition)
        if not contains_valid_state(condition):
            state_hallucination.append(condition)
    
            
    node_predicted_conditions = [condition for condition in predicted_conditions if is_node_condition(condition)]
    node_satisfied_conditions = [condition for condition in all_satisfied_conditions if is_node_condition(condition)]
    node_unsatisfied_conditions = [condition for condition in all_unsatisfied_conditions if is_node_condition(condition)]
    node_false_positive_conditions = [condition for condition in all_false_positive_conditions if is_node_condition(condition)]
    edge_predicted_conditions = [condition for condition in predicted_conditions if is_edge_condition(condition)]
    edge_satisfied_conditions = [condition for condition in all_satisfied_conditions if is_edge_condition(condition)]
    edge_unsatisfied_conditions = [condition for condition in all_unsatisfied_conditions if is_edge_condition(condition)]
    edge_false_positive_conditions = [condition for condition in all_false_positive_conditions if is_edge_condition(condition)]
    
    overall_confusion = compute_confusion_metrics(all_satisfied_conditions, all_unsatisfied_conditions, all_false_positive_conditions, predicted_conditions, keep_conditions=False)
    state_confusion = compute_confusion_metrics(node_satisfied_conditions, node_unsatisfied_conditions, node_false_positive_conditions, node_predicted_conditions, keep_conditions=False)
    spatial_confusion = compute_confusion_metrics(edge_satisfied_conditions, edge_unsatisfied_conditions, edge_false_positive_conditions, edge_predicted_conditions, keep_conditions=False)
    
    return {
        'grammatical_errors': 
            {
                "grammatically_valid_num": len(grammatically_valid_predicted_conditions),
                "grammatically_valid_rate": len(grammatically_valid_predicted_conditions) / len(predicted_conditions),
                "wrong_length_num": len(wrong_length),
                "wrong_length_rate": len(wrong_length) / len(predicted_conditions),
                "state_hallucination_num": len(state_hallucination),
                "state_hallucination_rate": len(state_hallucination) / len(predicted_conditions),
                "object_hallucination_num": num_object_hallucinations,
                "object_hallucination_rate": num_object_hallucinations / len(predicted_conditions),
            },
        'overall': 
            {
                "num_predicted_conditions": len(predicted_conditions),
                "num_GT_conditions": len(all_satisfied_conditions) + len(all_unsatisfied_conditions),
                "num_satisfied_conditions": len(all_satisfied_conditions),
                "num_unsatisfied_conditions": len(all_unsatisfied_conditions),
                "num_false_positive_conditions": len(all_false_positive_conditions),
                'overall_confusion_metrics': overall_confusion,
            },
        "state":
            {
                "num_predicted_conditions": len(node_predicted_conditions),
                "num_GT_conditions": len(node_satisfied_conditions) + len(node_unsatisfied_conditions),
                "num_satisfied_conditions": len(node_satisfied_conditions),
                "num_unsatisfied_conditions": len(node_unsatisfied_conditions),
                "num_false_positive_conditions": len(node_false_positive_conditions),
                'state_confusion_metrics': state_confusion,
            },
        "spatial":
            {
                "num_predicted_conditions": len(edge_predicted_conditions),
                "num_GT_conditions": len(edge_satisfied_conditions) + len(edge_unsatisfied_conditions),
                "num_satisfied_conditions": len(edge_satisfied_conditions),
                "num_unsatisfied_conditions": len(edge_unsatisfied_conditions),
                "num_false_positive_conditions": len(edge_false_positive_conditions),
                'spatial_confusion_metrics': spatial_confusion,
            },
    }



def per_demo_error_analysis(demo, all_satisfied_conditions, all_unsatisfied_conditions, all_false_positive_conditions, predicted_conditions):
    """Compute metrics for node and edge conditions separately."""
    
    grammatically_valid_predicted_conditions = []
    wrong_length = []
    state_hallucination = []
    object_hallucination = []
    for condition in predicted_conditions:
        if contains_valid_state(condition) and is_of_correct_length(condition) and contains_valid_objects(condition, demo):
            grammatically_valid_predicted_conditions.append(condition)
        if not is_of_correct_length(condition):
            wrong_length.append(condition)
        if not contains_valid_state(condition):
            state_hallucination.append(condition)
        if not contains_valid_objects(condition, demo):
            object_hallucination.append(condition)
            
    
            
    node_predicted_conditions = [condition for condition in predicted_conditions if is_node_condition(condition)]
    node_satisfied_conditions = [condition for condition in all_satisfied_conditions if is_node_condition(condition)]
    node_unsatisfied_conditions = [condition for condition in all_unsatisfied_conditions if is_node_condition(condition)]
    node_false_positive_conditions = [condition for condition in all_false_positive_conditions if is_node_condition(condition)]
    edge_predicted_conditions = [condition for condition in predicted_conditions if is_edge_condition(condition)]
    edge_satisfied_conditions = [condition for condition in all_satisfied_conditions if is_edge_condition(condition)]
    edge_unsatisfied_conditions = [condition for condition in all_unsatisfied_conditions if is_edge_condition(condition)]
    edge_false_positive_conditions = [condition for condition in all_false_positive_conditions if is_edge_condition(condition)]
    
    overall_confusion = compute_confusion_metrics(all_satisfied_conditions, all_unsatisfied_conditions, all_false_positive_conditions, predicted_conditions, keep_conditions=True)
    state_confusion = compute_confusion_metrics(node_satisfied_conditions, node_unsatisfied_conditions, node_false_positive_conditions, node_predicted_conditions, keep_conditions=True)
    spatial_confusion = compute_confusion_metrics(edge_satisfied_conditions, edge_unsatisfied_conditions, edge_false_positive_conditions, edge_predicted_conditions, keep_conditions=True)
    
    return {
        'grammatical_errors': 
            {
                "grammatically_valid_num": len(grammatically_valid_predicted_conditions),
                "grammatically_valid_rate": len(grammatically_valid_predicted_conditions) / len(predicted_conditions),
                "wrong_length_num": len(wrong_length),
                "wrong_length_rate": len(wrong_length) / len(predicted_conditions),
                "state_hallucination_num": len(state_hallucination),
                "state_hallucination_rate": len(state_hallucination) / len(predicted_conditions),
                "object_hallucination_num": len(object_hallucination),
                "object_hallucination_rate": len(object_hallucination) / len(predicted_conditions),
            },
        'overall': 
            {
                "num_predicted_conditions": len(predicted_conditions),
                "num_GT_conditions": len(all_satisfied_conditions) + len(all_unsatisfied_conditions),
                "num_satisfied_conditions": len(all_satisfied_conditions),
                "num_unsatisfied_conditions": len(all_unsatisfied_conditions),
                "num_false_positive_conditions": len(all_false_positive_conditions),
                'overall_confusion_metrics': overall_confusion,
            },
        "state":
            {
                "num_predicted_conditions": len(node_predicted_conditions),
                "num_GT_conditions": len(node_satisfied_conditions) + len(node_unsatisfied_conditions),
                "num_satisfied_conditions": len(node_satisfied_conditions),
                "num_unsatisfied_conditions": len(node_unsatisfied_conditions),
                "num_false_positive_conditions": len(node_false_positive_conditions),
                'state_confusion_metrics': state_confusion,
            },
        "spatial":
            {
                "num_predicted_conditions": len(edge_predicted_conditions),
                "num_GT_conditions": len(edge_satisfied_conditions) + len(edge_unsatisfied_conditions),
                "num_satisfied_conditions": len(edge_satisfied_conditions),
                "num_unsatisfied_conditions": len(edge_unsatisfied_conditions),
                "num_false_positive_conditions": len(edge_false_positive_conditions),
                'spatial_confusion_metrics': spatial_confusion,
            },
    }
    
    
def compute_confusion_metrics(all_satisfied_conditions, all_unsatisfied_conditions, all_false_positive_conditions, predicted_conditions, keep_conditions=True):
    
    # Compute evaluation metrics
    true_positives = len(all_satisfied_conditions)
    false_positives = len(all_false_positive_conditions)
    false_negatives = len(all_unsatisfied_conditions)
    accuracy = true_positives / len(predicted_conditions) if predicted_conditions else 0
    precision = true_positives / (true_positives + false_positives) if true_positives + false_positives > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if true_positives + false_negatives > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    
    if keep_conditions:
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'all_satisfied_conditions': all_satisfied_conditions,
            'all_unsatisfied_conditions': all_unsatisfied_conditions,
            'predicted_conditions': predicted_conditions,
            "false_positive_conditions": all_false_positive_conditions
        }
    else:
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score
        }




# define the evaluate dataset function
def evaluate_dataset(result_reference_list, save_path):
    all_satisfied_conditions = []
    all_unsatisfied_conditions = []
    all_predicted_conditions = []
    all_false_positive_conditions = []
    
    # because it is not possible to check illegal objects for each condition without demo name
    num_object_hallucination = 0

    # this is to store results for each individual demo
    model_results_evaluated = {}
    
    for tuple in result_reference_list:
        demo = tuple["identifier"]
        goal_conds = tuple["reference"]
        model_pred = tuple["llm_output"]
        
        satisfied_conditions, unsatisfied_conditions, false_positive_conditions, flattened_predicted_conditions = evaluate_goals(model_pred, goal_conds)
        model_results_evaluated[demo] = per_demo_error_analysis(demo, satisfied_conditions, unsatisfied_conditions, false_positive_conditions, flattened_predicted_conditions)
        num_object_hallucination += model_results_evaluated[demo]["grammatical_errors"]["object_hallucination_num"]
        
        all_satisfied_conditions.extend(satisfied_conditions)
        all_unsatisfied_conditions.extend(unsatisfied_conditions)
        all_false_positive_conditions.extend(false_positive_conditions)
        all_predicted_conditions.extend(flattened_predicted_conditions)
        
        
    # save results for each individual demo
    sorted_model_results_evaluated  = {key: model_results_evaluated [key] for key in sorted(model_results_evaluated)}
    with open(save_path, 'w') as json_file:
        json.dump(sorted_model_results_evaluated, json_file, indent=4)

    # this is to obtain error analysis results for the complete dataset
    dataset_results_evaluated = dataset_error_analysis(all_satisfied_conditions, all_unsatisfied_conditions, all_false_positive_conditions, all_predicted_conditions, num_object_hallucination)
    
    return dataset_results_evaluated





def main():
    
    result_reference_list_path = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/results/trial4/gpt4o_result_reference_list.json"
    save_path = "/Users/bryan/Desktop/wkdir/behavior-vllm-eval/igibson/evaluation/goal_interpretation/results/trial4/gpt4o_goal_interpretation_evaluated.json"
    
    # evaluate dataset:
    print(evaluate_dataset(result_reference_list_path, save_path))

if __name__ == "__main__":
    main()