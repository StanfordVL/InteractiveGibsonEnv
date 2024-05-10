# copied from https://github.com/zsyJosh/AgentEval/blob/shiyu_dev/virtualhome/simulation/evolving_graph/logic_score.py
# Author: Shiyu Zhao

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching
import re

class Expression:
    def evaluate(self, context):
        raise NotImplementedError("This method should be implemented by subclasses.")

class Literal(Expression):
    def __init__(self, name):
        self.name = name
    
    def evaluate(self, context):
        return context.get(self.name, False)
    
    def __repr__(self):
        return self.name

class Not(Expression):
    def __init__(self, expression):
        self.expression = expression
    
    def evaluate(self, context):
        return not self.expression.evaluate(context)
    
    def __repr__(self):
        return f"(not {self.expression})"

class And(Expression):
    def __init__(self, *args):
        self.args = args
    
    def evaluate(self, context):
        return all(arg.evaluate(context) for arg in self.args)
    
    def __repr__(self):
        return f"({' and '.join(map(str, self.args))})"

class Or(Expression):
    def __init__(self, *args):
        self.args = args
    
    def evaluate(self, context):
        return all(arg.evaluate(context) for arg in self.args)
    
    def __repr__(self):
        return f"({' or '.join(map(str, self.args))})"

class When(Expression):
    def __init__(self, condition, consequence):
        self.condition = condition
        self.consequence = consequence
    
    def evaluate(self, context):
        return self.consequence.evaluate(context) if self.condition.evaluate(context) else True
    
    def __repr__(self):
        return f"(when {self.condition} {self.consequence})"

class Exists(Expression):
    def __init__(self, variable, body):
        self.variable = variable
        self.body = body
    
    def evaluate(self, context):
        # Simplified evaluation logic for demonstration
        return all(self.body.evaluate({**context, self.variable: val}) for val in [True, False])
    
    def __repr__(self):
        return f"(exists {self.variable} {self.body})"

class Forall(Expression):
    def __init__(self, variable, body):
        self.variable = variable
        self.body = body
    
    def evaluate(self, context):
        # Simplified evaluation logic for demonstration
        return all(self.body.evaluate({**context, self.variable: val}) for val in [True, False])
    
    def __repr__(self):
        return f"(forall {self.variable} {self.body})"

def parse_expression(expression):
    if isinstance(expression, str) or isinstance(expression, bool):
        return Literal(str(expression))
    op, *args = expression
    if op == 'not':
        assert len(args) == 1, "NOT operator should have exactly one argument"
        return Not(parse_expression(args[0]))
    elif op == 'when':
        assert len(args) == 2, "WHEN operator should have exactly two arguments"
        return When(parse_expression(args[0]), parse_expression(args[1]))
    elif op == 'exists' or op == 'forall':
        assert len(args) == 2, "EXISTS and FORALL operators should have exactly two arguments"
        if op == 'exists':
            return Exists(args[0], parse_expression(args[1]))
        else:
            return Forall(args[0], parse_expression(args[1]))
    parsed_args = [parse_expression(arg) for arg in args]
    if op == 'and':
        return And(*parsed_args)
    elif op == 'or':
        return Or(*parsed_args)

def match_expressions(expr1, expr2):
    # Check for type and direct string comparison
    if isinstance(expr1, Literal) and isinstance(expr2, Literal):
        # print(f'string {expr1=}, string {expr2=}')
        return 1 if expr1.name == expr2.name else 0

    # print(f'{type(expr1)=}')
    # print(f'{type(expr2)=}')
    # print(f'{type(expr1) == type(expr2)=}')
    # Check class type and ensure both expressions are of the same type
    if type(expr1) != type(expr2):
        return 0
        
    # Handle Not, Exists, Forall expressions
    if isinstance(expr1, Not):
        return match_expressions(expr1.expression, expr2.expression)
    if isinstance(expr1, (Exists, Forall)):
        print(f'{expr1.variable=}, {expr2.variable=}')
        if expr1.variable == expr2.variable:
            return match_expressions(expr1.body, expr2.body)
        else:
            return 0
    # Handle And, Or expressions
    if isinstance(expr1, (And, Or)):
        sub1 = expr1.args
        sub2 = expr2.args
        size1, size2 = len(sub1), len(sub2)
        adj_matrix = np.zeros((size1, size2), dtype=int)
        
        for i in range(size1):
            for j in range(size2):
                adj_matrix[i, j] = match_expressions(sub1[i], sub2[j])

        sparse_matrix = csr_matrix(adj_matrix)
        match_result = maximum_bipartite_matching(sparse_matrix, perm_type='column')
        
        total_match = sum(adj_matrix[i, match_result[i]] for i in range(size1) if match_result[i] != -1)
        max_possible_match = min(size1, size2)
        
        return total_match / max_possible_match if max_possible_match > 0 else 0

    return 0

# Example use case
# Example 
# expr1 = parse_expression(('or', ('exists', 'x', 'y'), ('forall', 'y', ('or', 'c', 'd'))))
# expr2 = parse_expression(('or', ('exists', 'x', 'y'), False))

# score = match_expressions(expr1, expr2)
# print("Similarity Score:", score)


def tokenize(expression):
    # pattern = r'\(|\)|\b(and|or|not|exists|forall)\b|[\w-]+(?:\s[\?\w-]+)*'
    tokens = []
    buffer = ''
    
    for char in expression:
        if char in '()':
            if buffer:
                tokens.append(buffer.strip())
                buffer = ''
            tokens.append(char)
        elif re.match(r'\s', char):
            if buffer:
                buffer += char
        else:
            buffer += char
            
    # Add the last token if any
    if buffer:
        tokens.append(buffer.strip())
        
    return tokens

def parse_pddl_expr(tokens):
    stack = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == '(':
            stack.append(token)
        elif token == ')':
            if stack[-1] == '(':
                stack.pop()
                stack.append('()')
                i += 1
                continue
            subexpr = []
            while stack and stack[-1] != '(':
                subexpr.append(stack.pop())
            stack.pop()  # Remove the '('
            subexpr.reverse()

            # Determine how to process the collected subexpression
            if subexpr[0] in {'and', 'or'}:
                stack.append((subexpr[0], *subexpr[1:]))
            elif subexpr[0] == 'not':
                assert len(subexpr) == 2, "NOT should have exactly one argument"
                stack.append(('not', subexpr[1]))
            elif subexpr[0] in {'exists', 'forall'}:
                assert len(subexpr) == 3, "EXISTS and FORALL should have exactly two arguments"
                stack.append((subexpr[0], subexpr[1], subexpr[2]))
            elif subexpr[0] == 'when':
                assert len(subexpr) == 3, "WHEN should have exactly two arguments"
                stack.append(('when', subexpr[1], subexpr[2]))
            else:
                # print(f'{subexpr=}')
                stack.append(' '.join(subexpr))
        else:
            stack.append(token)
        i += 1

    if len(stack) == 1:
        return stack[0]
    else:
        raise Exception("Parsing error, check the structure of the input expression")

def parse_pddl_input(expression):
    tokens = tokenize(expression)
    # print(f'{tokens=}')
    return parse_pddl_expr(tokens)

def replace_in_tuple(tup, old_variable, new_variable):
    if not isinstance(tup, tuple):
        return tup.replace(old_variable, new_variable)
    
    return tuple(replace_in_tuple(item, old_variable, new_variable) for item in tup)


def align_expressions(expr1, expr2):
    if isinstance(expr1, str) and isinstance(expr2, str):
        return expr1, expr2
    if isinstance(expr1, str) or expr1 == '()':
        return expr1, expr2 if isinstance(expr2, tuple) else expr2
    if isinstance(expr2, str) or expr2 == '()':
        return expr1 if isinstance(expr1, tuple) else expr1, expr2

    if isinstance(expr1, tuple):
        op1, *args1 = expr1
    else:
        op1, args1 = expr1, []
    
    if isinstance(expr2, tuple):
        op2, *args2 = expr2
    else:
        op2, args2 = expr2, []
    
    aligned_args1, aligned_args2 = [], []

    if op1 == op2 and op1 in {'exists', 'forall'}:
        var1, body1 = args1
        var2, body2 = args2
        var1_name = var1.split('-')[0].strip()
        var2_name = var2.split('-')[0].strip()
        # recursively replace the variable name in the tuple
        var2 = replace_in_tuple(var2, var2_name, var1_name)
        body2 = replace_in_tuple(body2, var2_name, var1_name)
        aligned_args1.append(var1)
        aligned_args2.append(var2)
        aligned_args1.append(body1)
        aligned_args2.append(body2)
        return (op1, *aligned_args1), (op2, *aligned_args2)

    # Adjust behavior based on the operator type
    if op1 in {'and', 'or'} and op2 in {'and', 'or'}:
        max_length = max(len(args1), len(args2))
        for i in range(max_length):
            sub_expr1 = args1[i] if i < len(args1) else '()'
            sub_expr2 = args2[i] if i < len(args2) else '()'
            aligned_sub_expr1, aligned_sub_expr2 = align_expressions(sub_expr1, sub_expr2)
            aligned_args1.append(aligned_sub_expr1)
            aligned_args2.append(aligned_sub_expr2)
        return (op1, *aligned_args1), (op2, *aligned_args2)
    else:
        # For NOT, WHEN, FORALL, EXISTS, treat as atomic units
        return expr1, expr2


def calculate_logic_score(input_str1, input_str2):
    try:
        parsed_expression1 = parse_pddl_input(input_str1)
        parsed_expression2 = parse_pddl_input(input_str2)
        aligned_expr1, aligned_expr2 = align_expressions(parsed_expression1, parsed_expression2)
        expr1 = parse_expression(aligned_expr1)
        expr2 = parse_expression(aligned_expr2)
        score = match_expressions(expr1, expr2)
    except:
        print('Calculation failed!')
        print(f'{input_str1=}')
        print(f'{input_str2=}')
        score = 0.0
    return score


if __name__ == '__main__':
    # Example usage

    # input_str1 = "(and (grabbable ?obj) (next_to ?char ?obj))"
    # input_str2 = "(and (grabbable ?obj) (next_to ?char ?obj) (not (exists (?obj2 - object) (and (obj_inside ?obj ?obj2) (closed ?obj2)))) (not (and (exists (?obj3 - object) (holds_lh ?char ?obj3)) (exists (?obj4 - object) (holds_rh ?char ?obj4)))))"

    input_str1 = "(exists (?obj - object) (and (grabbable ?obj) (next_to ?char ?obj)))"
    input_str2 = "(exists (?target - object) (and (grabbable ?target) (next_to ?char ?target)))"

    # input_str1 = '(and () ())'
    # input_str2 = '()'

    print("Similarity Score:", calculate_logic_score(input_str1, input_str2))