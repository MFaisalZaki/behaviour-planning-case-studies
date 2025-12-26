from collections import defaultdict
from copy import deepcopy
import re
from z3 import ModelRef
from unified_planning.plans import SequentialPlan
from lark import Lark, Transformer, v_args
import os
import z3

from unified_planning.shortcuts import Fluent, BoolType, OperatorKind
from pypmt.encoders.utilities import str_repr
from behaviour_planning.over_domain_models.smt.bss.behaviour_features_library.base import DimensionConstructorSMT
from behaviour_planning.over_domain_models.smt.bss.behaviour_count.behaviour_counter_simulator import DimSimulator

class PossibleEndingsSimulator(DimSimulator):
    def __init__(self, task, addinfo):
        super().__init__(task, 'pe', {'vars': addinfo})

    def plan_behaviour(self, plan):
        return 'todo'


class PossibleEndingsSMT(DimensionConstructorSMT):
    def __init__(self, encoder, additional_information):
        self.flatten = lambda nested_list: [x for item in nested_list for x in (self.flatten(item) if isinstance(item, list) else [item])]
        self.features_predciates_vars = []
        super().__init__('Possible-Endings', encoder, additional_information)

    def __walk__(self, encoder, expr):
        match expr.node_type:
            case OperatorKind.AND | OperatorKind.OR:
                logic_operator = z3.And if expr.node_type == OperatorKind.AND else z3.Or    
                arity = [self.__walk__(encoder, a) for a in expr.args]
                operator_arity = list(filter(lambda e: (not callable(e)) and (z3.is_and(e) or z3.is_or(e) or z3.is_not(e)), self.flatten(arity)))
                if len(operator_arity) == 0:
                    operator_arity = list(filter(lambda e: not callable(e), self.flatten(arity)))
                return [logic_operator(operator_arity), arity]
            case OperatorKind.FLUENT_EXP:
                return encoder.up_fluent_to_z3[str_repr(expr)][-1]
            case OperatorKind.NOT:
                return z3.Not(self.__walk__(encoder, expr.args[0]))
            case _:
                assert False, 'The possible endings should be a conjunction of predicates.'


    def __encode__(self, encoder):
        for possible_ending in self.additional_information:
            possible_ending_vars = self.__walk__(encoder, possible_ending) # skip the first operator
            # collect variables in list
            self.features_predciates_vars.extend(filter(lambda e: not (callable(e) or z3.is_and(e) or z3.is_or(e) or z3.is_not(e)), self.flatten(possible_ending_vars)))
            # add the ending encodings.
            self.encodings.append(possible_ending_vars[0])

    def value(self, plan):
        ret_value = []
        ret_value_str = []
        if isinstance(plan, ModelRef):
            for predicate in self.features_predciates_vars:
                predicate_value = plan.evaluate(predicate, model_completion = True)
                ret_value.append(predicate == predicate_value)
                ret_value_str.append(f'({str(predicate == predicate_value)})')
        elif isinstance(plan, SequentialPlan):
            assert False, 'Value function is not implemented for this dimension for a plan.'
        else:
            raise TypeError(f"Unknown type for plan: {type(plan)}")
        self.var_domain.add(' ^ '.join(ret_value_str))
        assert not len(ret_value) == 0, "The ret_value should not be empty for the possible endings dimension"
        return z3.And(ret_value)
    
    def discretize(self, value):
        return value
    
    def behaviour_expression(self, plan):
        return self.discretize(self.value(plan))
