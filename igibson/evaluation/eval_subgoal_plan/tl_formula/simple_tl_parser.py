#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# File   : simple_tl_parser.py
# Author : Jiayuan Mao
# Email  : maojiayuan@gmail.com
# Date   : 04/11/2024
#
# Distributed under terms of the MIT license.

from typing import List

import lark
from lark import Transformer, v_args

import igibson.evaluation.eval_subgoal_plan.tl_formula.simple_tl as tl

grammar = r"""

?start: stmt

primitive: VARNAME "(" [args] ")"
object_name: VARNAME
           | VARNAMEWITHID
args: object_name ("," object_name)*

?stmt: then_stmt | primitive_stmt
then_stmt: or_stmt ("then" or_stmt)*
or_stmt: and_stmt ("or" and_stmt)*
and_stmt: primitive_stmt ("and" primitive_stmt)*
primitive_stmt: "not" primitive_stmt -> not_stmt
              | primitive
              | "(" stmt ")"
              | "forall" VARNAME "." "(" stmt ")" -> forall_stmt
              | "exists" VARNAME "." "(" stmt ")" -> exists_stmt
              | "forn" NUM "." VARNAME "." "(" stmt ")" -> forn_stmt

%import common.WS
%ignore WS
VARNAME: /[a-zA-Z_\-]\w*/
VARNAMEWITHID: /[a-zA-Z_\-]\w*\.[0-9]+/
NUM: /\d+/
"""

parser = lark.Lark(grammar, start='start')
inline_args = v_args(inline=True)


class SimpleTLTransformer(Transformer):
    def __init__(self, predicates: List[str], actions: List[str]):
        self.predicates = predicates
        self.actions = actions

    def start(self, stmt):
        return stmt

    @inline_args
    def primitive(self, name, args):
        if name in self.predicates:
            primitive = tl.Proposition(name, args)
        elif name in self.actions:
            primitive = tl.Action(name, args)
        else:
            raise ValueError(f'Unknown primitive: {name}')

        return tl.SimpleTLPrimitive(primitive)

    @inline_args
    def args(self, *args):
        return args
    
    @inline_args
    def object_name(self, name):
        return name

    @inline_args
    def not_stmt(self, stmt):
        return tl.SimpleTLNot(stmt)

    @inline_args
    def and_stmt(self, *stmts):
        if len(stmts) == 1:
            return stmts[0]
        return tl.SimpleTLAnd(*stmts)

    @inline_args
    def or_stmt(self, *stmts):
        if len(stmts) == 1:
            return stmts[0]
        return tl.SimpleTLOr(*stmts)

    @inline_args
    def then_stmt(self, *stmts):
        if len(stmts) == 1:
            return stmts[0]
        return tl.SimpleTLThen(*stmts)

    @inline_args
    def exists_stmt(self, var, stmt):
        return tl.SimpleTLExists(var, stmt)

    @inline_args
    def forall_stmt(self, var, stmt):
        return tl.SimpleTLForall(var, stmt)
    
    @inline_args
    def forn_stmt(self, num, var, stmt):
        return tl.SimpleTLForN(num, var, stmt)

    @inline_args
    def primitive_stmt(self, stmt):
        return stmt


def parse_simple_tl(text: str, predicates: List[str], actions: List[str]):
    tree = parser.parse(text)
    transformer = SimpleTLTransformer(predicates, actions)
    return transformer.transform(tree)


def test():
    predicates = ['P', 'Q', 'R', 'S']
    actions = ['A', 'B', 'C', 'D']

    text = 'P(obj1) and Q(obj2) or S(obj4.4, obj5.5, obj6.6) then R(obj3)'
    stmt = parse_simple_tl(text, predicates, actions)
    print(stmt)

    text = 'P(o1, o2) then ( (Q(o3) then R(o4.4)) or (S(o5.5, o6.6) then P(o7)) )'
    stmt = parse_simple_tl(text, predicates, actions)
    print(stmt)

    text = 'forall x. ( P(x) or exists y. ( P(x, y) and Q(x, y) ) ) then R(obj1) then exists x. (not P(x, y))'

    text = 'forn 2 x. ( P(x) or exists y. ( P(x, y) and Q(x, y) ) ) then R(obj1) then exists x. (not P(x, y))'
    try:
        stmt = parse_simple_tl(text, predicates, actions)
        print(stmt)
    except lark.exceptions.UnexpectedToken as e:
        print(f'Error type is {e.__class__.__name__}, error is {e}')
    except lark.exceptions.UnexpectedCharacters as e:
        print(f'Error type is {e.__class__.__name__}, error is {e}')
    except lark.exceptions.UnexpectedInput as e:
        print(f'Error type is {e.__class__.__name__}, error is {e}')
    except lark.exceptions.LexError as e:
        print(f'Error type is {e.__class__.__name__}, error is {e}')
    except lark.exceptions.ParseError as e:
        print(f'Error type is {e.__class__.__name__}, error is {e}')
    except Exception as e:
        print(f'Error type is {e.__class__.__name__}, error is {e}')
    finally:
        print("here")



if __name__ == '__main__':
    test()
