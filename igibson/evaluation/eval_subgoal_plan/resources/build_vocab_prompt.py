background_intro = \
'''# Background Introduction
You are determining the complete state transitions of a household task solving by a robot. The goal is to list all intermediate states (which is called subgoals as a whole) to achieve the final goal states from the initial states. The output consists of a list of boolean expression, which is a combination of the state predicates. Note that your output boolean expression list is in temporal order, therefore, it must be consistent and logical.'''

state_info = \
'''# Data Format Introduction
## Available States
The state is represented as a first-order predicate, which is a tuple of a predicate name and its arguments. Its formal definition looks like this "<PredicateName>(Params)", where <PredicateName> is the state name and each param should be ended with an id. An example is "inside(coin_1, jar_1)". Below is a list of available states and their descriptions.
| State Name | Arguments | Description |
| --- | --- | --- |
| inside | (obj1.id, obj2.id) | obj1 is inside obj2. If we have state inside(A, B), and you want to take A out of B while B is openable and stayed at "not open" state, please open B first. Also, inside(obj1, agent) is invalid.|
| ontop | (obj1.id, obj2.id) | obj1 is on top of obj2 |
| nextto | (obj1.id, obj2.id) | obj1 is next to obj2 |
| under | (obj1.id, obj2.id) | obj1 is under obj2 |
| onfloor | (obj1.id, floor2.id) | obj1 is on the floor2 |
| touching | (obj1.id, obj2.id) | obj1 is touching or next to obj2 |
| cooked | (obj1.id) | obj1 is cooked |
| burnt | (obj1.id) | obj1 is burnt |
| dusty | (obj1.id) | obj1 is dusty. If want to change dusty(obj1.id) to "not dusty(obj1.id)", there are two ways to do it, depending on task conditions. Here, all objects other than obj1 are types but not instances: 1. [inside(obj1.id, dishwasher or sink), toggleon(dishwasher or sink)] 2. holding other cleanning tool |
| frozen | (obj1.id) | obj1 is frozen |
| open | (obj1.id) | obj1 is open |
| sliced | (obj1.id) | obj1 is sliced. If want to change "not sliced(obj1.id)" to "sliced(obj1.id)", one must have a slicer. | 
| soaked | (obj1.id) | obj1 is soaked |
| stained | (obj1.id) | obj1 is stained. If want to change stained(obj1.id) to "not stained(obj1.id)", there are three ways to do it, depending on task conditions. Here, all objects other than obj1 are types but not instances: 1. [inside(obj1.id, sink), toggleon(sink)] 2. [soaked(cleaner)] 3. holding detergent. |
| toggleon | (obj1.id) | obj1 is toggled on |
| holds_rh | (obj1.id) | obj1 is in the right hand of the robot |
| holds_lh | (obj1.id) | obj1 is in the left hand of the robot |
## Available Connectives
The connectives are used to satisfy the complex conditions. They are used to combine the state predicates.
| Connective Name | Arguments | Description |
| --- | --- | --- |
| and | exp1 and exp2 | evaluates to true if both exp1 and exp2 are true |
| or | exp1 or exp2 | evaluates to true if either exp1 or exp2 is true |
| not | not exp | evaluates to true if exp is false |
| forall | forall(x, exp) | evaluates to true if exp is true for all x |
| exists | exists(x, exp) | evaluates to true if exp is true for at least one x |
| forpairs | forpairs(x, y, exp) | evaluates to true if exp is true for all pairs of x and y. For example, forpairs(watch, basket, inside(watch, basket)) means that for each watch and basket, the watch is inside the basket. |
| forn | forn(n, x, exp) | evaluates to true if exp is true for exactly n times for x. For example, forn(2, jar_n_01, (not open(jar_n_01)) means that there are exactly two jars that are not open. |
| fornpairs | fornpairs(n, x, y, exp) | evaluates to true if exp is true for exactly n times for pairs of x and y. For example, fornpairs(2, watch, basket, inside(watch, basket)) means that there are exactly two watches inside the basket. |
'''

supplement_info = \
'''## Supplement Information
- The initial states are the states that are given at the beginning of the task.
- Your output must be a list of boolean expressions that are in temporal order.
- You must follow the data format and the available states and connectives defined above.
- The output must be consistent, logical and as detailed as possible. View your output as a complete state transition from the initial states to the final goal states.
- For each line of the output, you should only output boolean expression, DO NOT INCLUDE IRRELEVANT INFORMATION (like number of line, explanation, etc.).
- Please note that the robot can only hold one object in one hand. Also, the robot needs to have at least one hand free to perform any action other than put, place, take, hold.
- Use holds_rh and holds_lh in your plan if necessary. For example, stained(shoe) cannot directly change to not stained(shoe), but needs intermediate states like [soaked(rag), holds_rh(rag), not stained(shoe)] or [holds_rh(detergent), not stained(shoe)].
- Do not output redundant states. A redundant state means a state that is either not necessary or has been satisfied before without broken. 
- Your output follows the temporal order line by line. If you think there is no temporal order requirement for certain states, you can use connective 'and' to combine them. If you think some states are equivalent, you can use connective 'or' to combine them.
- Please use provided relevant objects well to help you achieve the final goal states. Note that inside(obj1, agent) is an invalid state, therefore you cannot output it in your plan.
'''

gold_example_1 = \
'''# Example 1: Task is bottling_fruit
## Relevant objects in this scene
{'name': 'strawberry.0', 'category': 'strawberry_n_01'}
{'name': 'fridge.97', 'category': 'electric_refrigerator_n_01'}
{'name': 'peach.0', 'category': 'peach_n_03'}
{'name': 'countertop.84', 'category': 'countertop_n_01'}
{'name': 'jar.0', 'category': 'jar_n_01'}
{'name': 'jar.1', 'category': 'jar_n_01'}
{'name': 'carving_knife.0', 'category': 'carving_knife_n_01'}
{'name': 'bottom_cabinet_no_top.80', 'category': 'cabinet_n_01'}
{'name': 'room_floor_kitchen.0', 'category': 'floor_n_01'}

## Initial States
inside(strawberry.0, fridge.97)
inside(peach.0, fridge.97)
not sliced(strawberry.0)
not sliced(peach.0)
ontop(jar.0, countertop.84)
ontop(jar.1, countertop.84)
ontop(carving_knife.0, countertop.84)
onfloor(agent_n_01.1, room_floor_kitchen.0)

## Goal States
exists(jar_n_01, (inside(strawberry.0, jar_n_01) and (not inside(peach.0, jar_n_01))))
exists(jar_n_01, (inside(peach.0, jar_n_01) and (not inside(strawberry.0, jar_n_01))))
forall(jar_n_01, (not open(jar_n_01)))
sliced(strawberry.0)
sliced(peach.0)

## Output: Based on initial states, achieve final goal states logically and reasonably. It does not matter which state should be satisfied first, as long as all goal states can be satisfied at the end.
open(fridge.97)
ontop(strawberry.0, countertop.84) and ontop(peach.0, countertop.84)
holds_rh(carving_knife.0)
sliced(strawberry.0) and sliced(peach.0)
inside(strawberry.0, jar.0) and not inside(peach.0, jar.0)
inside(peach.0, jar.1) and not inside(strawberry.0, jar.1)
not open(jar.0) and not open(jar.1)
'''

target_task_into = \
f'''
# Target Task: <task_name>
## Relevant objects in this scene
<relevant_objects>

## Initial States
<initial_states>

## Goal States
<goal_states>

## Output: Based on initial states, achieve final goal states logically and reasonably. It does not matter which state should be satisfied first, as long as all goal states can be satisfied at the end.'''


import json
import os
def generate_prompt_scratch(prompt_file_path):
    if not os.path.exists(prompt_file_path):
        with open(prompt_file_path, 'w') as f:
            json.dump({}, f)
    with open(prompt_file_path, 'r') as f:
        prompts = json.load(f)
    prompts['Background'] = background_intro
    prompts['StateInfo'] = state_info
    prompts['SupplementInfo'] = supplement_info
    prompts['GoldExamples'] = []
    prompts['GoldExamples'].append(gold_example_1)
    prompts['TargetTask'] = target_task_into

    with open(prompt_file_path, 'w') as f:
        json.dump(prompts, f, indent=4)

if __name__ == '__main__':
    prompt_file_path = 'F:\\Projects\\Research\\embodiedAI\\kangrui\\iGibson\\igibson\\eval_subgoal_plan\\resources\\subgoal_plan_prompt_s_ltl.json'
    generate_prompt_scratch(prompt_file_path)
