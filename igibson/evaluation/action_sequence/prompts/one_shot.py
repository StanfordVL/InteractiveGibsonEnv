prompt="""

Problem:
You are designing instructions for a household robot. 
The goal is to guide the robot to modify its environment from an initial state to a desired final state. 
The input will be the initial environment state, the target environment state, the objects you can interact with in the environment. 
The output should be a list of action commands so that after the robot executes the action commands sequentially, the environment will change from the initial state to the target state. 

Data format: After # is the explanation.

Format of the states:
The environment state is a list starts with a uniary predicate or a binary prediate, followed by one or two obejcts.
You will be provided with multiple environment states as the initial state and the target state.
For example:
['inside', 'strawberry_0', 'fridge_97'] #strawberry_0 is inside fridge_97
['not', 'sliced', 'peach_0'] #peach_0 is not sliced
['ontop', 'jar_1', 'countertop_84'] #jar_1 is on top of countertop_84

Format of the action commands:
Action commands is a dictionary with the following format:
{{
        "action": "action_name", 
        "object": "target_obj_name",
}}

or 

{{
        "action": "action_name", 
        "object": "target_obj_name1,target_obj_name2",
}}

The action_name must be one of the following:
LEFT_GRASP # the robot grasps the object with its left hand, to execute the action, the robot's left hand must be empty, e.g. {{'action': 'LEFT_GRASP', 'object': 'apple_0'}}.
RIGHT_GRASP # the robot grasps the object with its right hand, to execute the action, the robot's right hand must be empty, e.g. {{'action': 'RIGHT_GRASP', 'object': 'apple_0'}}.
LEFT_PLACE_ONTOP # the robot places the object in its left hand on top of the target object and release the object in its left hand, e.g. {{'action': 'LEFT_PLACE_ONTOP', 'object': 'table_1'}}.
RIGHT_PLACE_ONTOP # the robot places the object in its right hand on top of the target object and release the object in its left hand, e.g. {{'action': 'RIGHT_PLACE_ONTOP', 'object': 'table_1'}}.
LEFT_PLACE_INSIDE # the robot places the object in its left hand inside the target object and release the object in its left hand, to execute the action, the robot's left hand must hold an object, and the target object can't be closed e.g. {{'action': 'LEFT_PLACE_INSIDE', 'object': 'fridge_1'}}.
RIGHT_PLACE_INSIDE # the robot places the object in its right hand inside the target object and release the object in its left hand, to execute the action, the robot's right hand must hold an object, and the target object can't be closed, e.g. {{'action': 'RIGHT_PLACE_INSIDE', 'object': 'fridge_1'}}.
RIGHT_RELEASE # the robot directly releases the object in its right hand, to execute the action, the robot's left hand must hold an object, e.g. {{'action': 'RIGHT_RELEASE', 'object': 'apple_0'}}.
LEFT_RELEASE # the robot directly releases the object in its left hand, to execute the action, the robot's right hand must hold an object, e.g. {{'action': 'LEFT_RELEASE', 'object': 'apple_0'}}.
OPEN # the robot opens the target object, to execute the action, the target object should be openable and closed, also, toggle off the target object first if want to open it, e.g. {{'action': 'OPEN', 'object': 'fridge_1'}}.
CLOSE # the robot closes the target object, to execute the action, the target object should be openable and open, e.g. {{'action': 'CLOSE', 'object': 'fridge_1'}}.
COOK # the robot cooks the target object, to execute the action, the target object should be put in a pan, e.g. {{'action': 'COOK', 'object': 'apple_0'}}.
CLEAN # the robot cleans the target object, to execute the action, the robot should have a cleaning tool such as rag, the cleaning tool should be soaked if possible, or the target object should be put into a toggled on cleaner like a sink or a dishwasher, e.g. {{'action': 'CLEAN', 'object': 'window_0'}}.
FREEZE # the robot freezes the target object e.g. {{'action': 'FREEZE', 'object': 'apple_0'}}.
UNFREEZE # the robot unfreezes the target object, e.g. {{'action': 'UNFREEZE', 'object': 'apple_0'}}.
SLICE # the robot slices the target object, to execute the action, the robot should have a knife in hand, e.g. {{'action': 'SLICE', 'object': 'apple_0'}}.
SOAK # the robot soaks the target object, to execute the action, the target object must be put in a toggled on sink, e.g. {{'action': 'SOAK', 'object': 'rag_0'}}.
DRY # the robot dries the target object, e.g. {{'action': 'DRY', 'object': 'rag_0'}}.
TOGGLE_ON # the robot toggles on the target object, to execute the action, the target object must be closed if the target object is openable and open e.g. {{'action': 'TOGGLE_ON', 'object': 'light_0'}}.
TOGGLE_OFF # the robot toggles off the target object, e.g. {{'action': 'TOGGLE_OFF', 'object': 'light_0'}}.
LEFT_PLACE_NEXTTO # the robot places the object in its left hand next to the target object and release the object in its left hand, e.g. {{'action': 'LEFT_PLACE_NEXTTO', 'object': 'table_1'}}.
RIGHT_PLACE_NEXTTO # the robot places the object in its right hand next to the target object and release the object in its right hand, e.g. {{'action': 'RIGHT_PLACE_NEXTTO', 'object': 'table_1'}}.
LEFT_TRANSFER_CONTENTS_INSIDE # the robot transfers the contents in the object in its left hand inside the target object, e.g. {{'action': 'LEFT_TRANSFER_CONTENTS_INSIDE', 'object': 'bow_1'}}.
RIGHT_TRANSFER_CONTENTS_INSIDE # the robot transfers the contents in the object in its right hand inside the target object, e.g. {{'action': 'RIGHT_TRANSFER_CONTENTS_INSIDE', 'object': 'bow_1'}}.
LEFT_TRANSFER_CONTENTS_ONTOP # the robot transfers the contents in the object in its left hand on top of the target object, e.g. {{'action': 'LEFT_TRANSFER_CONTENTS_ONTOP', 'object': 'table_1'}}.
RIGHT_TRANSFER_CONTENTS_ONTOP # the robot transfers the contents in the object in its right hand on top of the target object, e.g. {{'action': 'RIGHT_TRANSFER_CONTENTS_ONTOP', 'object': 'table_1'}}.
LEFT_PLACE_NEXTTO_ONTOP # the robot places the object in its left hand next to target object 1 and on top of the target object 2 and release the object in its left hand, e.g. {{'action': 'LEFT_PLACE_NEXTTO_ONTOP', 'object': 'window_0, table_1'}}.
RIGHT_PLACE_NEXTTO_ONTOP # the robot places the object in its right hand next to object 1 and on top of the target object 2 and release the object in its right hand, e.g. {{'action': 'RIGHT_PLACE_NEXTTO_ONTOP', 'object': 'window_0, table_1'}}.
LEFT_PLACE_UNDER # the robot places the object in its left hand under the target object and release the object in its left hand, e.g. {{'action': 'LEFT_PLACE_UNDER', 'object': 'table_1'}}.
RIGHT_PLACE_UNDER # the robot places the object in its right hand under the target object and release the object in its right hand, e.g. {{'action': 'RIGHT_PLACE_UNDER', 'object': 'table_1'}}.

Format of the interactable objects:
Interactable object will contain multiple lines, each line is a dictionary with the following format:
{{
    "name": "object_name",
    "category": "object_category"
}}
object_name is the name of the object, which you must use in the action command, object_category is the category of the object, which provides a hint for you in interpreting initial and goal condtions.

Please pay specail attention:
1. The robot can only hold one object in each hand.
2. Action name must be one of the above action names, and the object name must be one of the object names listed in the interactable objects.
3. All PLACE actions will release the object in the robot's hand, you don't need to explicitly RELEASE the object after the PLACE action.
4. For LEFT_PLACE_NEXTTO_ONTOP and RIGHT_PLACE_NEXTTO_ONTOP, the action command are in the format of {{'action': 'action_name', 'object': 'obj_name1, obj_name2'}}
5. If you want to perform an action to an target object, you must make sure the target object is not inside a closed object.
6. For actions like OPEN, CLOSE, SLICE, COOK, CLEAN, SOAK, DRY, FREEZE, UNFREEZE, TOGGLE_ON, TOGGLE_OFF, at least one of the robot's hands must be empty, and the target object must have the corresponding property like they're openable, toggleable, etc.
7. For PLACE actions and RELEASE actions, the robot must hold an object in the corresponding hand.
8. Before slicing an object, the robot can only interact with the object (e.g. peach_0), after slicing the object, the robot can only interact with the sliced object (e.g. peach_0_part_0).


Examples: after# is the explanation.

Example 1:
Input:
initial environment state:
['stained', 'sink_7']
['stained', 'bathtub_4']
['not', 'soaked', 'rag_0']
['onfloor', 'rag_0', 'room_floor_bathroom_0']
['inside', 'rag_0', 'cabinet_1']
['not', 'open', 'cabinet_1']


target environment state:
['not', 'stained', 'bathtub_4']
['not', 'stained', 'sink_7']
['and', 'soaked', 'rag_0', 'inside', 'rag_0', 'bucket_0']


interactable objects:
{{'name': 'sink_7', 'category': 'sink.n.01'}}
{{'name': 'bathtub_4', 'category': 'bathtub.n.01'}}
{{'name': 'bucket_0', 'category': 'bucket.n.01'}}
{{'name': 'rag_0', 'category': 'rag.n.01'}}
{{'name': 'cabinet_1', 'category': 'cabinet.n.01'}}


Please output the list of action commands (in the given format) so that after the robot executes the action commands sequentially, the current environment state will change to target environment state. Usually, the robot needs to execute multiple action commands consecutively to achieve final state. Please output multiple action commands rather than just one. Only output the list of action commands with nothing else.

Output:
[
    {{
        "action": "OPEN",
        "object": "cabinet_1"
    }}, # you want to get the rag_0 from cabinet_1, should open it first
    {{
        "action": "RIGHT_GRASP",
        "object": "rag_0"
    }}, # you want to clean the sink_7 and bathtub_4, you found them stained, so you need to soak the rag_0 first
    {{
        "action": "RIGHT_PLACE_INSIDE",
        "object": "sink_7"
    }}, # to soak the rag_0, you need to place it inside the sink_7
    {{
        "action": "TOGGLE_ON",
        "object": "sink_7"
    }}, # to soak the rag_0, you need to toggle on the sink_7
    {{
        "action": "SOAK",
        "object": "rag_0"
    }}, # now you can soak the rag_0
    {{
        "action": "TOGGLE_OFF",
        "object": "sink_7"
    }}, # after soaking the rag_0, you need to toggle off the sink_7
    {{
        "action": "LEFT_GRASP",
        "object": "rag_0"
    }}, # now you can grasp soaked rag_0 to clean stain
    {{
        "action": "CLEAN",
        "object": "sink_7"
    }}, # now you clean the sink_7
    {{
        "action": "CLEAN",
        "object": "bathtub_4"
    }}, # now you clean the bathtub_4
    {{
        "action": "LEFT_PLACE_INSIDE",
        "object": "bucket_0"
    }} # after cleaning the sink_7, you need to place the rag_0 inside the bucket_0
]

Your task:
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
    print(prompt.format(init_state=123,target_state=456,obj_list="123"))
    