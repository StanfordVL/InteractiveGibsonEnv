zero_shot="""
You are designing instructions for a household robot. 
The goal is to guide the robot to modify its environment from an initial state to a desired final state. 
The input will be the initial environment state, the target environment state, the objects you can interact with in the environment. 
The output should be a list of action commands so that after the robot executes the action commands sequentially, the environment will change from the initial state to the target state. 

Data format: After # is the explanation.

The environment state is a list starts with a uniary predicate or a binary prediate, followed by one or two obejcts.
You will be provided with multiple environment states as the initial state and the target state.
For example:
['inside', 'strawberry_0', 'fridge_97'] #strawberry_0 is inside fridge_97
['not', 'sliced', 'peach_0'] #peach_0 is not sliced
['ontop', 'jar_1', 'countertop_84'] #jar_1 is on top of countertop_84


Action commands is a dictionary with the following format:
{{
        "action": "action_name", 
        "object": "obj_name",
}}
The action_name can be one of the following:

LEFT_GRASP # the robot grasps the object with its left hand, e.g. {{'action': 'LEFT_GRASP', 'object': 'apple_0'}}
RIGHT_GRASP # the robot grasps the object with its right hand, e.g. {{'action': 'RIGHT_GRASP', 'object': 'apple_0'}}
LEFT_PLACE_ONTOP # the robot places the object in its left hand on top of another object and release it, e.g. {{'action': 'LEFT_PLACE_ONTOP', 'object': 'table_1'}}
RIGHT_PLACE_ONTOP # the robot places the object in its right hand on top of another object and release it, e.g. {{'action': 'RIGHT_PLACE_ONTOP', 'object': 'table_1'}}
LEFT_PLACE_INSIDE # the robot places the object in its left hand inside another object and release it, e.g. {{'action': 'LEFT_PLACE_INSIDE', 'object': 'fridge_1'}}
RIGHT_PLACE_INSIDE # the robot places the object in its right hand inside another object and release it, e.g. {{'action': 'RIGHT_PLACE_INSIDE', 'object': 'fridge_1'}}
RIGHT_RELEASE # the robot directly releases the object in its right hand, e.g. {{'action': 'RIGHT_RELEASE', 'object': 'apple_0'}}
LEFT_RELEASE # the robot directly releases the object in its left hand, e.g. {{'action': 'LEFT_RELEASE', 'object': 'apple_0'}}
OPEN # the robot opens an object, e.g. {{'action': 'OPEN', 'object': 'fridge_1'}}
CLOSE # the robot closes an object, e.g. {{'action': 'CLOSE', 'object': 'fridge_1'}}
BURN # the robot burns an object, e.g. {{'action': 'BURN', 'object': 'apple_0'}}
COOK # the robot cooks an object, e.g. {{'action': 'COOK', 'object': 'apple_0'}}
CLEAN # the robot cleans an object, e.g. {{'action': 'CLEAN', 'object': 'window_0'}}
FREEZE # the robot freezes an object, e.g. {{'action': 'FREEZE', 'object': 'apple_0'}}
UNFREEZE # the robot unfreezes an object, e.g. {{'action': 'UNFREEZE', 'object': 'apple_0'}}
SLICE # the robot slices an object, e.g. {{'action': 'SLICE', 'object': 'apple_0'}}
SOAK # the robot soaks an object, e.g. {{'action': 'SOAK', 'object': 'rag_0'}}
DRY # the robot dries an object, e.g. {{'action': 'DRY', 'object': 'rag_0'}}
TOGGLE_ON # the robot toggles an object on, e.g. {{'action': 'TOGGLE_ON', 'object': 'light_0'}}
TOGGLE_OFF # the robot toggles an object off, e.g. {{'action': 'TOGGLE_OFF', 'object': 'light_0'}}
UNCLEAN # the robot unclean an object, e.g. {{'action': 'UNCLEAN', 'object': 'window_0'}}
LEFT_PLACE_NEXTTO # the robot places the object in its left hand next to another object and release it, e.g. {{'action': 'LEFT_PLACE_NEXTTO', 'object': 'table_1'}}
RIGHT_PLACE_NEXTTO # the robot places the object in its right hand next to another object and release it, e.g. {{'action': 'RIGHT_PLACE_NEXTTO', 'object': 'table_1'}}
LEFT_TRANSFER_CONTENTS_INSIDE # the robot transfers the contents in the object in its left hand inside another object, e.g. {{'action': 'LEFT_TRANSFER_CONTENTS_INSIDE', 'object': 'bow_1'}}
RIGHT_TRANSFER_CONTENTS_INSIDE # the robot transfers the contents in the object in its right hand inside another object, e.g. {{'action': 'RIGHT_TRANSFER_CONTENTS_INSIDE', 'object': 'bow_1'}}
LEFT_TRANSFER_CONTENTS_ONTOP # the robot transfers the contents in the object in its left hand on top of another object, e.g. {{'action': 'LEFT_TRANSFER_CONTENTS_ONTOP', 'object': 'table_1'}}
RIGHT_TRANSFER_CONTENTS_ONTOP # the robot transfers the contents in the object in its right hand on top of another object, e.g. {{'action': 'RIGHT_TRANSFER_CONTENTS_ONTOP', 'object': 'table_1'}}
LEFT_PLACE_NEXTTO_ONTOP # the robot places the object in its left hand next to one object and on top of the other object and release it, e.g. {{'action': 'LEFT_PLACE_NEXTTO_ONTOP', 'object': 'window_0, table_1'}}
RIGHT_PLACE_NEXTTO_ONTOP # the robot places the object in its right hand next to one object and on top of the other object and release it, e.g. {{'action': 'RIGHT_PLACE_NEXTTO_ONTOP', 'object': 'window_0, table_1'}}
LEFT_PLACE_UNDER # the robot places the object in its left hand under another object and release it, e.g. {{'action': 'LEFT_PLACE_UNDER', 'object': 'table_1'}}
RIGHT_PLACE_UNDER # the robot places the object in its right hand under another object and release it, e.g. {{'action': 'RIGHT_PLACE_UNDER', 'object': 'table_1'}}

The action_name should be upper case.
Except for LEFT_PLACE_NEXTTO_ONTOP, RIGHT_PLACE_NEXTTO_ONTOP, the object should be a single object.
The obj_name must exactly match one of the names given below in the interactable obejcts.

Interactable object will contain multiple lines, each line is a dictionary with the following format:
{{
    "name": "object_name",
    "category": "object_category"
}}
object_name is the name of the object, which you must use in the action command, object_category is the category of the object, which provides a hint for you in interpreting initial and goal condtions.

Input:
initial environment state:
{init_state}

target environment state:
{target_state}

interactable objects:
{obj_list}

Please output the list of action commands (in the given format) so that after the robot executes the action commands sequentially, the current environment state will change to target environment state. Usually, the robot needs to execute multiple action commands consecutively to achieve final state. Please output multiple action commands rather than just one. Only output the list of action commands with nothing else.

Output:


"""


if __name__ == "__main__":
    print(zero_shot.format(cur_state=123,target_state=456,obj_list="123"))