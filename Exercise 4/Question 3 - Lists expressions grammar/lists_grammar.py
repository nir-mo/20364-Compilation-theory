# File: ouplpr.py
#
# Date: 10 - December - 2018
#
# Implementation of the lists expressions grammar.
#
# Author: Nir Moshe.

from lark import Lark, Transformer, v_args


__author__ = "Nir Moshe"


LISTS_EXPRESSIONS_GRAMMAR = r"""
    start: S
    
    S: ITEM
    
    ITEM: "sum(" L ")"      
      | "max(" L ")"   
      | NUMBER
    
    L: "[" ITEMLIST "]" 
        | "tail(" L ")" 
        | "cons(" ITEM "," L ")"
        | "insert(" ITEM "," ITEM "," L ")"
        
    ITEMLIST: (ITEM ",")+ | ITEM | EPSILON
              
    // Tokens
    NUMBER: /[0-9]+/
    EPSILON: /1/
"""

class ListsExpressionsTransformer(Transformer):
    def sum_list(self, *args, **kwargs):
        pass

    def max_list(self, *args, **kwargs):
        pass

    def value(self, *args, **kwargs):
        pass

    def S(self, matches):
        pass
        return matches[0]


parser = Lark(LISTS_EXPRESSIONS_GRAMMAR)



def test():
    tree = parser.parse("sum([1])")
    new_tree = ListsExpressionsTransformer().transform(tree)



if __name__ == '__main__':
    test()
