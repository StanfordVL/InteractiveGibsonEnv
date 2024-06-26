import bddl
import json
from typing import List, Dict
from bddl.condition_evaluation import HEAD

def translate_tl_obj_into_addressable_obj(tl_obj):
    addressable_obj = tl_obj.replace('.', '_')
    return addressable_obj

def translate_addressable_obj_into_tl_obj(address_obj):
    if 'toggled' in address_obj:
        return 'toggledon'
    if '_' not in address_obj:
        return address_obj
    # replace the last char '_' with '.'
    address_obj = address_obj.replace('.', '_')
    parts = address_obj.split('_')
    assert len(parts) > 1, 'Invalid addressable object name: {}'.format(address_obj)
    tl_obj = '_'.join(parts[:-1]) + '.' + parts[-1]
    return tl_obj

def replace_wildcard_name(bddl_body:List, name_to_replace:str, special_symbol_id:int):
    new_bddl_body = []
    special_symbol = f'x{special_symbol_id}'
    for part in bddl_body:
        if isinstance(part, list):
            new_part = replace_wildcard_name(part, name_to_replace, special_symbol_id)
            new_bddl_body.append(new_part)
        elif isinstance(part, str):
            if part == name_to_replace:
                new_bddl_body.append(special_symbol)
            else:
                new_bddl_body.append(part)
        else:
            raise ValueError(f'Invalid part type: {part} in bddl_body {bddl_body}')
    return new_bddl_body

def build_tl_expr_from_bddl_condition_recursively(bddl_body:List, special_symbol_id=0, level=0) -> str:
    connective_or_primitive = bddl_body[0]
    if connective_or_primitive == 'exists' or connective_or_primitive == 'forall':
        category_name = bddl_body[1][2]
        special_symbol = f'x{special_symbol_id}'
        exists_body = replace_wildcard_name(bddl_body[2], category_name, special_symbol_id)
        special_symbol_id += 1
        tl_exists_body = build_tl_expr_from_bddl_condition_recursively(exists_body, special_symbol_id, level+1)
        connective_name = connective_or_primitive
        tl_expr = f'{connective_name} {special_symbol}. (not {category_name}({special_symbol}) or {tl_exists_body})'
        if level > 0:
            tl_expr = f'({tl_expr})'
    elif connective_or_primitive == 'forn':
        num = bddl_body[1][0]
        category_name = bddl_body[2][2]
        special_symbol = f'x{special_symbol_id}'
        exists_body = replace_wildcard_name(bddl_body[3], category_name, special_symbol_id)
        special_symbol_id += 1
        tl_exists_body = build_tl_expr_from_bddl_condition_recursively(exists_body, special_symbol_id, level+1)
        connective_name = 'forn'
        tl_expr = f'{connective_name} {num}. {special_symbol}. (not {category_name}({special_symbol}) or {tl_exists_body})'
        if level > 0:
            tl_expr = f'({tl_expr})'
    elif connective_or_primitive == 'forpairs':
        category_name_1 = bddl_body[1][2]
        category_name_2 = bddl_body[2][2]
        special_symbol_1 = f'x{special_symbol_id}'
        special_symbol_2 = f'x{special_symbol_id+1}'
        exists_body = replace_wildcard_name(bddl_body[3], category_name_1, special_symbol_id)
        exists_body = replace_wildcard_name(exists_body, category_name_2, special_symbol_id+1)
        special_symbol_id += 2
        tl_exists_body = build_tl_expr_from_bddl_condition_recursively(exists_body, special_symbol_id, level+1)
        tl_expr_1 = f'forall {special_symbol_1}. (not {category_name_1}({special_symbol_1}) or forn 1. {special_symbol_2}. (not {category_name_2}({special_symbol_2}) or {tl_exists_body}))'
        tl_expr_2 = f'forall {special_symbol_2}. (not {category_name_2}({special_symbol_2}) or forn 1. {special_symbol_1}. (not {category_name_1}({special_symbol_1}) or {tl_exists_body}))'
        tl_expr = f'{tl_expr_1} and {tl_expr_2}'
        if level > 0:
            tl_expr = f'({tl_expr})'
    elif connective_or_primitive == 'fornpairs':
        num = bddl_body[1][0]
        category_name_1 = bddl_body[2][2]
        category_name_2 = bddl_body[3][2]
        special_symbol_1 = f'x{special_symbol_id}'
        special_symbol_2 = f'x{special_symbol_id+1}'
        exists_body = replace_wildcard_name(bddl_body[4], category_name_1, special_symbol_id)
        exists_body = replace_wildcard_name(exists_body, category_name_2, special_symbol_id+1)
        special_symbol_id += 2
        tl_exists_body = build_tl_expr_from_bddl_condition_recursively(exists_body, special_symbol_id, level+1)
        tl_expr_1 = f'forn {num}. {special_symbol_1}. (not {category_name_1}({special_symbol_1}) or forn 1. {special_symbol_2}. (not {category_name_2}({special_symbol_2}) or {tl_exists_body}))'
        tl_expr_2 = f'forn {num}. {special_symbol_2}. (not {category_name_2}({special_symbol_2}) or forn 1. {special_symbol_1}. (not {category_name_1}({special_symbol_1}) or {tl_exists_body}))'
        tl_expr = f'{tl_expr_1} and {tl_expr_2}'
        if level > 0:
            tl_expr = f'({tl_expr})'
    elif connective_or_primitive == 'and':
        and_statements = [build_tl_expr_from_bddl_condition_recursively(part, special_symbol_id, level+1) for part in bddl_body[1:]]
        tl_expr = ' and '.join(and_statements)
        if level > 0:
            tl_expr = f'({tl_expr})'
    elif connective_or_primitive == 'or':
        or_statements = [build_tl_expr_from_bddl_condition_recursively(part, special_symbol_id, level+1) for part in bddl_body[1:]]
        tl_expr = ' or '.join(or_statements)
        if level > 0:
            tl_expr = f'({tl_expr})'
    elif connective_or_primitive == 'not':
        not_statement = build_tl_expr_from_bddl_condition_recursively(bddl_body[1], special_symbol_id, level+1)
        tl_expr = f'not {not_statement}'
        if level > 0:
            tl_expr = f'({tl_expr})'
    else:
        primitive_name = connective_or_primitive
        params = ', '.join(bddl_body[1:])
        tl_expr = f'{primitive_name}({params})'
    return tl_expr


def translate_raw_bddl_name_rep_into_tl_name_rep(name_mapping:Dict[str, Dict], tl_category_map:Dict[str, str], bddl_body:List):
    new_bddl_body = []
    for part in bddl_body:
        if isinstance(part, list):
            new_part = translate_raw_bddl_name_rep_into_tl_name_rep(name_mapping, tl_category_map, part)
            new_bddl_body.append(new_part)
        elif isinstance(part, str):
            part = part.strip('?')
            part = name_mapping[part]['name'] if part in name_mapping else part
            if part in tl_category_map:
                new_bddl_body.append(tl_category_map[part])
            else:
                new_bddl_body.append(translate_addressable_obj_into_tl_obj(part))
        else:
            raise ValueError(f'Invalid part type: {part} in bddl_body {bddl_body}')

    return new_bddl_body

def remove_redudant_list(bddl_body:List):
    new_bddl_body = []
    for part in bddl_body:
        if isinstance(part[0], list) and len(part) == 1:
            new_part = remove_redudant_list(part[0])
            new_bddl_body.append(new_part)
        else:
            new_bddl_body.append(part)
    return new_bddl_body if not isinstance(new_bddl_body[0], list) or len(new_bddl_body) > 1 else new_bddl_body[0]

def translate_bddl_condition_into_tl(name_mapping:Dict[str, Dict], tl_category_map:Dict[str, str], bddl_condition:HEAD, flatten=False):
    if flatten == False:
        bddl_body = bddl_condition.body
        bddl_body = translate_raw_bddl_name_rep_into_tl_name_rep(name_mapping, tl_category_map, bddl_body)
        tl_expr = build_tl_expr_from_bddl_condition_recursively(bddl_body)
    else:
        flatten_bddl_body = remove_redudant_list(bddl_condition.flattened_condition_options)
        connective = bddl_condition.body[0]
        if connective == 'exists' and isinstance(flatten_bddl_body[0], list):
            if isinstance(flatten_bddl_body[0][0], list):
                tmp = []
                for i in range(len(flatten_bddl_body)):
                    row_tmp = None
                    if len(flatten_bddl_body[i]) > 1:
                        row_tmp = ['and'] + flatten_bddl_body[i]
                    else:
                        row_tmp = flatten_bddl_body[i]
                    tmp.append(row_tmp)
                if len(tmp) > 1:
                    flatten_bddl_body = ['or'] + tmp
                else:
                    flatten_bddl_body = tmp[0]
            else:
                flatten_bddl_body = ['or'] + flatten_bddl_body
        elif connective == 'forall' and isinstance(flatten_bddl_body[0], list):
            # flatten_bddl_body = ['and'] + flatten_bddl_body
            if isinstance(flatten_bddl_body[0][0], list):
                tmp = []
                for i in range(len(flatten_bddl_body)):
                    row_tmp = []
                    if len(flatten_bddl_body[i]) > 1:
                        row_tmp = ['and'] + flatten_bddl_body[i]
                    else:
                        row_tmp = flatten_bddl_body[i]
                    tmp.append(row_tmp)
                if len(tmp) > 1:
                    flatten_bddl_body = ['and'] + tmp
                else:
                    flatten_bddl_body = tmp[0]
            else:
                flatten_bddl_body = ['and'] + flatten_bddl_body
        elif connective == 'forn' and isinstance(flatten_bddl_body[0], list):
            num = int(bddl_condition.body[1][0])
            if num > 1:
                tmp = []
                for item in flatten_bddl_body:
                    tmp.append(['and'] + item)
                if len(tmp) > 1:
                    flatten_bddl_body = ['or'] + tmp
            else:
                flatten_bddl_body = ['or'] + flatten_bddl_body
        elif connective == 'forpairs' and isinstance(flatten_bddl_body[0], list):
            tmp = []
            for i in range(len(flatten_bddl_body)):
                row_tmp = []
                if len(flatten_bddl_body[i]) > 1:
                    row_tmp = ['and'] + flatten_bddl_body[i]
                else:
                    row_tmp = flatten_bddl_body[i]
                tmp.append(row_tmp)
            if len(tmp) > 1:
                flatten_bddl_body = ['or'] + tmp
            else:
                flatten_bddl_body = tmp[0]
        elif connective == 'fornpairs' and isinstance(flatten_bddl_body[0], list):
            num = int(bddl_condition.body[1][0])
        else:
            if isinstance(flatten_bddl_body[0], list):
                flatten_bddl_body = ['and'] + flatten_bddl_body
        flatten_bddl_body = translate_raw_bddl_name_rep_into_tl_name_rep(name_mapping, tl_category_map, flatten_bddl_body)
        try:
            tl_expr = build_tl_expr_from_bddl_condition_recursively(flatten_bddl_body)
        except Exception as e:
            print(f'Error in translating bddl condition into tl: {bddl_condition}')
            print(f'Error message: {e}')
            raise e
    return tl_expr

def translate_bddl_final_states_into_tl(name_mapping:Dict[str, Dict], tl_category_map:Dict[str, str], bddl_goal_conditions:List[HEAD], flatten=False):
    tl_goal_conditions = []
    for bddl_condition in bddl_goal_conditions:
        tl_expr = translate_bddl_condition_into_tl(name_mapping, tl_category_map, bddl_condition, flatten)
        tl_goal_conditions.append(tl_expr)
    return tl_goal_conditions


def build_simplified_tl_expr_from_bddl_condition_recursively(bddl_body:List, level=0) -> str:
    connective_or_primitive = bddl_body[0]
    if connective_or_primitive == 'exists' or connective_or_primitive == 'forall':
        category_name = bddl_body[1][2]
        exists_body = bddl_body[2]
        s_tl_exists_body = build_simplified_tl_expr_from_bddl_condition_recursively(exists_body, level+1)
        connective_name = connective_or_primitive
        s_tl_expr = f'{connective_name}({category_name}, {s_tl_exists_body})'
    elif connective_or_primitive == 'forn':
        num = bddl_body[1][0]
        category_name = bddl_body[2][2]
        exists_body = bddl_body[3]
        s_tl_exists_body = build_simplified_tl_expr_from_bddl_condition_recursively(exists_body, level+1)
        connective_name = 'forn'
        s_tl_expr = f'forn({num}, {category_name}, {s_tl_exists_body})'
    elif connective_or_primitive == 'forpairs':
        category_name_1 = bddl_body[1][2]
        category_name_2 = bddl_body[2][2]
        exists_body = bddl_body[3]
        s_tl_exists_body = build_simplified_tl_expr_from_bddl_condition_recursively(exists_body, level+1)
        s_tl_expr = f'forpairs({category_name_1}, {category_name_2}, {s_tl_exists_body})'
    elif connective_or_primitive == 'fornpairs':
        num = bddl_body[1][0]
        category_name_1 = bddl_body[2][2]
        category_name_2 = bddl_body[3][2]
        exists_body = bddl_body[4]
        s_tl_exists_body = build_simplified_tl_expr_from_bddl_condition_recursively(exists_body, level+1)
        s_tl_expr = f'fornpairs({num}, {category_name_1}, {category_name_2}, {s_tl_exists_body})'
    elif connective_or_primitive == 'and':
        and_statements = [build_simplified_tl_expr_from_bddl_condition_recursively(part, level+1) for part in bddl_body[1:]]
        s_tl_expr = ' and '.join(and_statements)
        if level > 0:
            s_tl_expr = f'({s_tl_expr})'
    elif connective_or_primitive == 'or':
        or_statements = [build_simplified_tl_expr_from_bddl_condition_recursively(part, level+1) for part in bddl_body[1:]]
        s_tl_expr = ' or '.join(or_statements)
        if level > 0:
            s_tl_expr = f'({s_tl_expr})'
    elif connective_or_primitive == 'not':
        not_statement = build_simplified_tl_expr_from_bddl_condition_recursively(bddl_body[1], level+1)
        s_tl_expr = f'not {not_statement}'
        if level > 0:
            s_tl_expr = f'({s_tl_expr})'
    else:
        primitive_name = connective_or_primitive
        params = ', '.join(bddl_body[1:])
        s_tl_expr = f'{primitive_name}({params})'
    return s_tl_expr

def translate_bddl_condition_into_simplified_tl(name_mapping:Dict[str, Dict], tl_category_map:Dict[str, str], bddl_condition:HEAD):
    bddl_body = bddl_condition.body
    bddl_body = translate_raw_bddl_name_rep_into_tl_name_rep(name_mapping, tl_category_map, bddl_body)
    s_tl_expr = build_simplified_tl_expr_from_bddl_condition_recursively(bddl_body)
    return s_tl_expr

def translate_bddl_final_states_into_simplified_tl(name_mapping:Dict[str, Dict], tl_category_map:Dict[str, str], bddl_goal_conditions:List[HEAD]):
    s_tl_goal_conditions = []
    for bddl_condition in bddl_goal_conditions:
        s_tl_expr = translate_bddl_condition_into_simplified_tl(name_mapping, tl_category_map, bddl_condition)
        s_tl_goal_conditions.append(s_tl_expr)
    return s_tl_goal_conditions