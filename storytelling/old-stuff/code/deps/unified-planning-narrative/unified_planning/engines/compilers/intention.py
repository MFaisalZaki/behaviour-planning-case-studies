"""This module defines the dnf remover class."""

from collections import OrderedDict, defaultdict
from copy import deepcopy
import itertools

import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.shortcuts import OperatorKind
from unified_planning.engines.compilers.utils import (
    lift_action_instance,
    create_action_with_given_subs,
)

from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    AbstractProblem,
    FNode,
    Fluent,
    Effect,
    Problem,
    BoolExpression,
    NumericConstant,
    InstantaneousAction,
    DurativeAction,
    TimeInterval,
    Timing,
    Action,
    ProblemKind,
    Oversubscription,
    TemporalOversubscription,
    generate_causal_graph,
    types
)
from unified_planning.model.variable import Variable
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.model.walkers import Dnf
from typing import Iterator, List, Optional, Tuple, Dict, cast
from itertools import product
from functools import partial

from enum import Enum

class IntentionCompiler(engines.engine.Engine, CompilerMixin):
    """
    IntentionCompiler transforms an `Intentional Planning Problem` into a `Classical Planning Problem`.

    For now, this compilation is based on Haslum's compilation presented in Patrik Haslum (2012).
    """

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, None)

    @property
    def name(self):
        return "IntentionCompiler"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("INT_FLUENTS")
        supported_kind.set_fluents_type("REAL_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= IntentionCompiler.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == compilation_kind.INTENTIONAL_REMOVING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = problem_kind.clone()
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: Optional[CompilationKind] = None,
    ) -> CompilerResult:
        """
        Takes an instance of a :class:`~unified_planning.model.Problem`
        and returns a `CompilerResult` where the intentional planning problem is compiled into a classical `Problem`.

        :param problem: The instance of the `Problem` that must be returned without disjunctive conditions.
        :param compilation_kind: Not used for now.
        :return: The resulting `CompilerResult` data structure.
        """
        assert isinstance(problem, Problem)

        env = problem.environment

        old_to_new: Dict[up.model.Fluent, up.model.Fluent] = {}
        new_fluents: List["up.model.Fluent"] = []

        self.intentional_actions = defaultdict(list)

        new_problem = problem.clone()
        new_problem.name = f"{problem.name}"
        new_problem.clear_fluents()
        new_problem.clear_actions()
        new_problem.clear_goals()
        new_problem.clear_timed_goals()
        new_problem.clear_timed_effects()
        new_problem.clear_quality_metrics()
        new_problem.initial_values.clear()
                
        # Step 1: create the intends, delegated and justified fluents.
        self._create_intend_delegate_justify_fluents(problem, new_problem)
        
        # Step 2: Initialise the new problem with the fluents, initial values and goal.
        self._init_fluents(problem, new_problem)
        self._init_goals(problem, new_problem)

        # Step 3: Compile actions.
        for action in problem.actions:
            for compiled_action in self._compile_action(action, problem, new_problem):
                new_problem.add_action(compiled_action)
        
        # TODO: Find a way to create this map.
        trace_back_map: Dict[Action, Tuple[Action, List[FNode]]] = {}

        return CompilerResult(
            new_problem,
            partial(lift_action_instance, map=trace_back_map),
            engine_name=self.name,
        )
    
    def _compile_action(self, action:Action, problem: Problem, new_problem: Problem) -> List[Action]:
        
        compiled_actions_list = []

        action_effect_fluents = set(map(lambda e: e.fluent if e.fluent.node_type in [OperatorKind.FLUENT_EXP] else e.fluent.args[0].fluent, action.effects))
        action_effect_fluents = set(map(lambda f: f._content.payload, action_effect_fluents))
        
        # get the actions effects.
        if len(action.actors) == 0:
            # This ia a happening action, don't compile it.
            if not 'intends' in set(map(lambda e: self._flatten_args(e.fluent).name, action.effects)): return [action.clone()]
            # Else this action has an intends effect, update the intends effect.
            compiled_act = action.clone()
            compiled_act.clear_effects()
            for effect in self.__process_intends_in_action_effects__(action, new_problem):
                compiled_act.add_effect(effect.fluent, effect.value, effect.condition, forall=effect.forall)
            return [compiled_act]

        # this action receives an intention as an argument. This has a different way of compilation.
        if 'fact' in [p.type.name for p in action.parameters]:
            return self.__generate_action_intention_delegate__(action, problem, new_problem)
        
        # Else we need to compile the effect and delegateion effect if needed.
        common_intendable_effects = set.intersection(set(problem._intendable_fluents), 
                                                     set(problem._delegatable_fluents),
                                                     action_effect_fluents)
        if len(common_intendable_effects) > 0:
            for intention in common_intendable_effects:
                compiled_actions_list.extend(self.__compile_intention_for_action(intention, action, problem, new_problem, True))

        for intention in problem._intendable_fluents:
            compiled_actions_list.extend(self.__compile_intention_for_action(intention, action, problem, new_problem, False))

        return compiled_actions_list

    def __compile_intention_for_action(self, intend:Fluent, act:Action, prob:Problem, newprob:Problem, use_same_args:bool) -> List[Action]:
        _env = newprob.environment
        _em  = _env.expression_manager
        parameter_obj = up.model.parameter.Parameter

        compiled_actions_list = []
        for idx, actor in act.actors:
                base_name = f'{act.name}-because-{actor.name}-intends-{intend.name}' if not use_same_args else f'{act.name}-because-{actor.name}-{idx}-intends-{intend.name}'
                extended_args = [] if use_same_args else [parameter_obj(f'{intend.name}-{arg.name}', arg.type, _env) for arg in intend.signature]

                parameters = OrderedDict()
                for p in act.parameters + extended_args: parameters[p.name] = p.type
                compiled_action = InstantaneousAction(base_name, parameters, _env)
                
                # Step 2: Construct the preconditions.
                for precondition in act.preconditions:
                    # combine the intends in the preconditions.
                    predicates  = list(filter(lambda p: 'intends' not in str(p), precondition.args)) if precondition.node_type in [OperatorKind.AND, OperatorKind.OR] else [precondition]
                    predicates += [self.__resolve_intention_as_precondition__(p, newprob) for p in list(filter(lambda p: 'intends' in str(p), precondition.args))]
                    predicates += self.__process_delegate_precondition_expr__(actor, act, prob, newprob, use_same_args)
                    predicates += self.__process_intends_precondition_expr__(precondition, intend, actor, act, compiled_action, newprob)
                    #predicates = list(filter(lambda p: p != _em.true_expression, predicates))
                    if precondition.node_type in [OperatorKind.AND, OperatorKind.FLUENT_EXP, OperatorKind.NOT]:  predicates = _em.And(predicates)
                    elif precondition.node_type == OperatorKind.OR: predicates = _em.Or(predicates)
                    else: raise Exception(f"Unexpected node type: {precondition.node_type}")
                    compiled_action.add_precondition(predicates)

                # Step 3: Construct the effects.
                for eff in self.__process_intends_in_action_effects__(act, newprob):
                    compiled_action.add_effect(eff.fluent, eff.value, eff.condition, forall=eff.forall)
                    
                compiled_actions_list.append(compiled_action)

        return compiled_actions_list

    def __resolve_intention_as_precondition__(self, intendprecondition:FNode, newprob:Problem):
        _em = newprob.environment.expression_manager
        precond = intendprecondition.args[-1] if intendprecondition.node_type in [OperatorKind.NOT] else intendprecondition
        fluentname, args = self._combine_(precond)
        # Skip the case where the intend is an expression.
        if 'fact' in [p.type.name for p in args]: return _em.true_expression
        fluent = list(filter(lambda f: f.name == f'{fluentname}', newprob.fluents))[0]
        return _em.Not(_em.FluentExp(fluent, args)) if intendprecondition.node_type in [OperatorKind.NOT] else _em.FluentExp(fluent, args)

    def __resolve_intention_as_args__(self, actor, act:Action, intendprecondition:FNode, intention:FNode, newprob: Problem) -> FNode:
        _em = newprob.environment.expression_manager
        precond = intendprecondition.args[-1] if intendprecondition.node_type in [OperatorKind.NOT] else intendprecondition
        fluentname, args = self._combine_(precond)
        # Skip the case where the intend is an expression.
        if not 'fact' in [p.type.name for p in args]: return _em.true_expression
        # get the intention paramters from the compiled action.
        args = []
        for prefix in ['', 'i-']:
            args = [p for p in act.parameters if p.name.startswith(f'{prefix}{intention.name}-')]
            if len(args) > 0: break
        assert len(args) > 0, f"Intend arguments not found for {intention.name} in {act.name}"
        fluent = list(filter(lambda f: f.name == f'intends-{intention.name}', newprob.fluents))[0]
        return _em.FluentExp(fluent, [actor] + args)

    def __generate_action_intention_delegate__(self, act:Action, prob: Problem, newprob: Problem) -> List[Action]:
        _env = newprob.environment
        _em  = _env.expression_manager
        parameter_obj = up.model.parameter.Parameter
        
        generated_actions = []
        for idx, actor in act.actors:
            for delegate, intention in itertools.product(prob._delegatable_fluents, prob._intendable_fluents):

                base_name = f'{act.name}-{delegate.name}-because-intends-{intention.name}'
                action_args = list(filter(lambda arg: arg.type.name != 'fact', act.parameters))

                # append the delegate and intend parameters.
                prefix_delegate = 'd-' if delegate.name == intention.name else ''
                prefix_intend   = 'i-' if delegate.name == intention.name else ''

                delegate_args = [parameter_obj(f'{prefix_delegate}{delegate.name}-{arg.name}', arg.type, _env) for arg in delegate.signature]
                intend_args   = [parameter_obj(f'{prefix_intend}{intention.name}-{arg.name}', arg.type, _env) for arg in intention.signature]

                # Step 1: Contruct the parameters.
                parameters = OrderedDict()
                for p in action_args + delegate_args + intend_args: parameters[p.name] = p.type
                compiled_act = InstantaneousAction(base_name, parameters, _env)

                # Contruct the delegate precondition.
                delegated_fluent = list(filter(lambda f: f.name == f'delegated-{delegate.name}', newprob.fluents))[0]
                character_variable = Variable('c', delegate.signature[0].type, _env)
                delegate_expr = _em.Not(_em.FluentExp(delegated_fluent, [character_variable] + delegate_args))
                delegate_preconditions = [_em.Forall(delegate_expr, *[character_variable])]

                # Contruct the intend precondition.
                intend_fluent = list(filter(lambda f: f.name == f'intends-{intention.name}', newprob.fluents))[0]
                intend_expr = _em.FluentExp(intend_fluent, [parameter_obj(actor.name, actor.type, _env)] + intend_args)
                intend_preconditions = [intend_expr]

                # Step 2: Construct the preconditions.
                for precondition in act.preconditions:
                    # combine the intends in the preconditions.
                    predicates  = list(filter(lambda p: 'intends' not in str(p), precondition.args)) if precondition.node_type in [OperatorKind.AND, OperatorKind.OR] else [precondition]
                    predicates += [self.__resolve_intention_as_precondition__(p, newprob) for p in list(filter(lambda p: 'intends' in str(p), precondition.args))]
                    # predicates += [self.__resolve_intention_as_args__(actor, compiled_act, p, intention, newprob) for p in list(filter(lambda p: 'intends' in str(p), precondition.args))]
                    predicates += delegate_preconditions
                    predicates += intend_preconditions
                    #predicates = list(filter(lambda p: p != _em.true_expression, predicates))
                    if precondition.node_type in [OperatorKind.AND, OperatorKind.FLUENT_EXP, OperatorKind.NOT]:  predicates = _em.And(predicates)
                    elif precondition.node_type == OperatorKind.OR: predicates = _em.Or(predicates)
                    else: raise Exception(f"Unexpected node type: {precondition.node_type}")
                    compiled_act.add_precondition(predicates)
                
                # Step 3: Construct the effects.
                effectlist = []
                # First we need to get all the characters inside the action that is not the actor.
                intend_eff_fluent = list(filter(lambda f: f.name == f'intends-{delegate.name}', newprob.fluents))[0]
                for actor_arg in filter(lambda a: (a == actor), act.parameters):
                    delegate_expr_ = _em.FluentExp(delegated_fluent, [actor_arg] + delegate_args)
                    effectlist.append(up.model.effect.Effect(*_em.auto_promote(delegate_expr_, not (actor_arg.name == actor.name), True)))
                    if (actor_arg.name == actor.name): continue # don't add intend effect for the actor.
                    intend_expr = _em.FluentExp(intend_eff_fluent, [actor_arg] + delegate_args)
                    effectlist.append(up.model.effect.Effect(*_em.auto_promote(intend_expr, True, True)))
                        
                # now append non-intends effects.
                for eff in filter(lambda e: 'intends(' not in str(e.fluent), act.effects):
                    effectlist.append(eff)
                
                for eff in effectlist:
                    compiled_act.add_effect(eff.fluent, eff.value, eff.condition, forall=eff.forall)
                    
                generated_actions.append(compiled_act)
        return generated_actions

    def __process_intends_in_action_effects__(self, act: Action, newprob: Problem) -> set[FNode]:
        _em  = newprob.environment.expression_manager
        updated_effects = set()
        # Keep the non-intends effects.
        for eff in filter(lambda e: not 'intends(' in str(e.fluent), act.effects):
            updated_effects.add(eff)
        # Update the intends effects.
        for eff in filter(lambda e: 'intends(' in str(e.fluent), act.effects):
            _effect_condition = eff.condition
            if eff.condition.node_type != OperatorKind.BOOL_CONSTANT and 'intends(' in str(eff.condition):
                # check if the condition has an intention then condition will need to be updated.
                match eff.condition.node_type:
                    case OperatorKind.AND | OperatorKind.OR:
                        non_intend_conditions = list(filter(lambda c: 'intends(' not in str(c), eff.condition.args))
                        intends_conditions = []
                        for cond in filter(lambda c: 'intends(' in str(c), eff.condition.args):
                            _fluentname, _args = self._combine_(cond)
                            _fluent = list(filter(lambda f: f.name == _fluentname, newprob.fluents))[0]
                            intends_conditions.append(_em.FluentExp(_fluent, _args))
                        _effect_condition = _em.And(*non_intend_conditions, *intends_conditions) if eff.condition.node_type == OperatorKind.AND else _em.Or(*non_intend_conditions, *intends_conditions)
                    case OperatorKind.FLUENT_EXP:
                        _fluentname, _args = self._combine_(cond)
                        _fluent = list(filter(lambda f: f.name == _fluentname, newprob.fluents))[0]
                        _effect_condition = _em.FluentExp(_fluent, _args)
                    case _:
                        raise Exception(f"Unexpected conditional effect node type: {eff.condition.node_type}")
            flunetname, args = self._combine_(eff.fluent)
            eff_intention_fluent = list(filter(lambda f: f.name == flunetname, newprob.fluents))[0]
            updated_effects.add(up.model.effect.Effect(*_em.auto_promote(_em.FluentExp(eff_intention_fluent, args), eff.value, _effect_condition), forall=eff.forall))
        return updated_effects

    def __process_delegate_precondition_expr__(self, actor, act: Action, prob: Problem, newprob: Problem, no_intender: bool) -> set[FNode]:
        expr_retlist = []
        _env = newprob.environment
        _em  = _env.expression_manager
        action_effect_fluents = set(map(lambda e: (e, e.fluent) if e.fluent.node_type in [OperatorKind.FLUENT_EXP] else (e, e.fluent.args[0].fluent), act.effects))
        for common_effect_delegate in set.intersection(set(prob._delegatable_fluents), set(map(lambda f: f[-1]._content.payload, action_effect_fluents))):
            delegated_fluent = list(filter(lambda f: f.name == f'delegated-{common_effect_delegate.name}', newprob.fluents))[0]
            for eff, value in map(lambda e: (e[0].fluent, e[0].value), filter(lambda e: e[1]._content.payload == common_effect_delegate, action_effect_fluents)):
                    if not value._content.payload: continue # skip the negative effects.
                    character_variable = Variable('c', delegated_fluent.signature[0].type, _env)
                    delegate_expr = _em.Not(_em.FluentExp(delegated_fluent, [character_variable] + list(eff.args)))
                    if no_intender:
                        expr_retlist.append(_em.Forall(_em.Implies(_em.Not(_em.Equals(character_variable, actor)), delegate_expr), *[character_variable]))
                    else:
                        expr_retlist.append(_em.Forall(delegate_expr, *[character_variable]))
        return expr_retlist

    def __process_delegate_effect_expr__(self, actor, delegate:Fluent, act: Action, prob: Problem, newprob: Problem) -> set[FNode]:
        expr_retlist = []
        _env = newprob.environment
        _em = _env.expression_manager
        parameter_obj = up.model.parameter.Parameter
        
        action_effect_fluents = map(lambda e: (e, e.fluent) if e.fluent.node_type in [OperatorKind.FLUENT_EXP] else (e, e.fluent.args[0].fluent), act.effects)
        action_effect_fluents = filter(lambda e: e[0].value._content.payload, action_effect_fluents)
        action_effect_fluents = set(filter(lambda e: e[1]._content.payload == delegate, action_effect_fluents))
        
        delegate_fluent = list(filter(lambda f: f.name == f'delegated-{delegate.name}', newprob.fluents))[0]
        for eff, eff_fluent in action_effect_fluents:
            expr_retlist.append(_em.FluentExp(delegate_fluent, [parameter_obj(actor.name, actor.type, _env)] + list(eff_fluent.args)))
        return expr_retlist
    
    def __process_intends_precondition_expr__(self, precondition:FNode, intend:Fluent, actor, act:Action, newact: Action, newprob: Problem) -> set[FNode]:
        expr_retlist = []
        _env = newprob.environment
        _em = _env.expression_manager
        parameter_obj = up.model.parameter.Parameter
        intend_fluent = list(filter(lambda f: f.name == f'intends-{intend.name}', newprob.fluents))[0]
        args = list(filter(lambda a: a in newact.parameters, [parameter_obj(f'{intend.name}-{arg.name}', arg.type, _env) for arg in intend.signature]))
        if len(args) == 0:
            # First check the effect if not then check the preconditions.
            # get the intends effects with true value and ignore the false values.
            action_effect_fluents = map(lambda e: (e, e.fluent) if e.fluent.node_type in [OperatorKind.FLUENT_EXP] else (e, e.fluent.args[0].fluent), act.effects)
            # remove the false fluents values.
            action_effect_fluents = filter(lambda e: e[0].value._content.payload, action_effect_fluents)
            action_effect_fluents = set(filter(lambda e: e[1]._content.payload == intend, action_effect_fluents))
            for eff, eff_fluent in action_effect_fluents:
                expr_retlist.append(_em.FluentExp(intend_fluent, [parameter_obj(actor.name, actor.type, _env)] + list(eff_fluent.args)))
            # check if this intend is a precondition so we can get those arguments from the action.
            if len(action_effect_fluents) == 0:
                possible_fluent = list(filter(lambda f: 'intends(' in str(f), precondition.args))
                if len(possible_fluent) > 0:
                    possible_fluent = possible_fluent[0]
                    args = possible_fluent.args[-1].args[-1] if possible_fluent.args[-1].node_type in [OperatorKind.NOT] else possible_fluent.args[-1]
                    args = list(args.args)
                    expr_retlist.append(_em.FluentExp(intend_fluent, [parameter_obj(actor.name, actor.type, _env)] + args))
        else:
            expr_retlist.append(_em.FluentExp(intend_fluent, [parameter_obj(actor.name, actor.type, _env)] + args))
        return expr_retlist
    
    def __get_primary_type__(self,objtype):
        if hasattr(objtype, 'type'):
            if objtype.type.father is None: return objtype
            return self.__get_primary_type__(objtype.type.father)
        elif hasattr(objtype, 'father'):
            if objtype.father is None: return objtype
            return self.__get_primary_type__(objtype.father)
        else:
            assert False, f"Unexpected node type: {objtype.node_type}"
        
    def _flatten_args(self, expr: FNode) -> List[FNode]:
        if isinstance(expr, Effect):
            return self._flatten_args(expr.fluent)
        if expr.node_type == OperatorKind.FLUENT_EXP:
            return expr._content.payload
        elif expr.node_type == OperatorKind.NOT:
            return self._flatten_args(expr.args[0])
        elif expr.node_type == OperatorKind.EQUALS:
            return None
        elif expr.node_type in [OperatorKind.AND, OperatorKind.OR]:
            ret_predicates = set()
            for arg in expr.args:
                ret_predicates.add(self._flatten_args(arg))
            # remove the None values.
            return set(filter(lambda x: x is not None, ret_predicates))
        else:
            raise Exception(f"Unexpected node type: {expr.node_type}")

    def _create_intend_delegate_justify_fluents(self, problem: Problem, new_problem: Problem) -> None:
        
        _tm  = new_problem.environment.type_manager
        _env = new_problem.environment
        parameter_obj = up.model.parameter.Parameter

        actor_type = list(filter(lambda t: t.name == 'character', new_problem.user_types))
        assert len(actor_type) == 1, "There should be only one type named 'character' in the domain to represent the actors."

        # First add the other fluents.
        recompiled_fluents = ['intends', 'delegated', 'justified']
        for fluent in filter(lambda f: not (f.name in recompiled_fluents), problem.fluents): 
            new_problem.add_fluent(fluent)

        _created_intend_fluents   = set()
        _created_delegate_fluents = set()

        # add the negated intends and delegated fluents.
        # append the negated fluents if exists in the problem.
        for intend in problem._negated_intendable_fluents:
            fluent = list(filter(lambda f: f.name == intend.replace('not-', ''), new_problem._fluents))[0]
            args  = []
            args += [parameter_obj(name, arg, _env) for name, arg in [(f'{intend}-{a.name}', a.type) for a in fluent.signature]]
            problem._intendable_fluents.append(up.model.Fluent(f'not-{fluent.name}', _tm.BoolType(), args, _env))
            if f'intends-not-{fluent.name}' in [f.name for f in new_problem._fluents]: continue
            intends_fluent = up.model.Fluent(f'intends-not-{fluent.name}', _tm.BoolType(), [parameter_obj('intender', actor_type[0], _env)] + args, _env)
            new_problem.add_fluent(intends_fluent)
            _created_intend_fluents.add(intends_fluent.name)
        
        for delegate in problem._negated_delegatable_fluents:
            fluent = list(filter(lambda f: f.name == delegate.replace('not-', ''), new_problem._fluents))[0]
            args  = []
            args += [parameter_obj(name, arg, _env) for name, arg in [(f'{delegate}-{a.name}', a.type) for a in fluent.signature]]
            problem._delegatable_fluents.append(up.model.Fluent(f'not-{fluent.name}', _tm.BoolType(), args, _env))
            if f'delegated-not-{fluent.name}' in [f.name for f in new_problem._fluents]: continue
            delegated_fluent = up.model.Fluent(f'delegated-not-{fluent.name}', _tm.BoolType(), [parameter_obj('intender', actor_type[0], _env)] + args, _env)
            new_problem.add_fluent(delegated_fluent)
            _created_delegate_fluents.add(delegated_fluent.name)
        
        pass

        for delegate, intend in itertools.product(problem._delegatable_fluents, problem._intendable_fluents):
            # We need to create the JUSTIFIED predicate for each intend and delegate.
            for key in ['-', '-not-']:
            # for key in ['-']:
                fluentname = f'intends{key}{intend.name}'
                if not fluentname in _created_intend_fluents: 
                    args  = [parameter_obj('intender', actor_type[0], _env)]
                    # args += [parameter_obj(name, arg, _env) for name, arg in [(f'{intend.name}-{a.name}', self.__get_primary_type__(a.type)) for a in intend.signature]]
                    args += [parameter_obj(name, arg, _env) for name, arg in [(f'{intend.name}-{a.name}', a.type) for a in intend.signature]]
                    fluent = up.model.Fluent(fluentname, _tm.BoolType(), args, _env)
                    new_problem.add_fluent(fluent)
                    _created_intend_fluents.add(fluentname)

                fluentname = f'delegated{key}{delegate.name}'
                if not fluentname in _created_delegate_fluents:
                    args  = [parameter_obj('intender', actor_type[0], _env)]
                    # args += [parameter_obj(name, arg, _env) for name, arg in [(f'{delegate.name}-{a.name}', self.__get_primary_type__(a.type)) for a in delegate.signature]]
                    args += [parameter_obj(name, arg, _env) for name, arg in [(f'{delegate.name}-{a.name}', a.type) for a in delegate.signature]]
                    fluent = up.model.Fluent(fluentname, _tm.BoolType(), args, _env)
                    new_problem.add_fluent(fluent)
                    _created_delegate_fluents.add(fluentname)

                # # Create the jistifed predicate.
                # fluentname = f'justified-{delegate.name}{key}{intend.name}'
                # args  = [parameter_obj('intender', actor_type[0], _env)]
                # args += [parameter_obj(name, arg, _env) for name, arg in [(f'{delegate.name}-{a.name}', self.__get_primary_type__(a.type)) for a in delegate.signature]]
                # args += [parameter_obj(name, arg, _env) for name, arg in [(f'{intend.name}-{a.name}',   self.__get_primary_type__(a.type)) for a in intend.signature]]
                # fluent = up.model.Fluent(fluentname, _tm.BoolType(), args, _env)
                # new_problem.add_fluent(fluent)

    def _init_fluents(self, problem: Problem, new_problem: Problem) -> None:
        _em  = new_problem.environment.expression_manager

        intend_delegate = filter(lambda p: p._content.payload.name in ['intends', 'delegated'], problem.initial_values)
        for predicate in filter(lambda p: p.args[-1].node_type != OperatorKind.BOOL_CONSTANT, intend_delegate):
            fluentname, args = self._combine_(predicate)
            # get fluent from the name.
            fluent = list(filter(lambda f: f.name == fluentname, new_problem.fluents))
            assert len(fluent) == 1, f"Fluent {fluentname} not found in the new problem."
            new_problem.set_initial_value(_em.FluentExp(fluent[0], args), problem.initial_values[predicate])
        
        # Now add the other initial values.
        for predicate in filter(lambda p: p._content.payload.name not in ['intends', 'delegated'], problem.initial_values):
            fluent = list(filter(lambda f: f.name == predicate._content.payload.name, new_problem.fluents))
            assert len(fluent) == 1, f"Fluent {predicate._content.payload.name} not found in the new problem."
            new_problem.set_initial_value(_em.FluentExp(fluent[0], predicate.args), problem.initial_values[predicate])

    def _init_goals(self, problem: Problem, new_problem: Problem) -> None:
        for goal in problem.goals:
            assert not any(['intend' in g for g in [str(g) for g in goal.args]]), "Goals with intends are not supported."
            new_problem.add_goal(goal)

    def _combine_(self, expr: FNode) -> Tuple[str, List[str]]:
        if expr.node_type == OperatorKind.FLUENT_EXP:
            name = expr._content.payload.name
            if name == 'intends':
                fact_names, fact_args  = self._combine_(expr.args[1]) 
                return f'intends-{fact_names}', [expr.args[0]] + fact_args
            else:
                name = expr._content.payload.name
                args = list(expr.args)
                return name, args
        elif expr.node_type == OperatorKind.NOT:
            fact_names, fact_args = self._combine_(expr.args[0])
            return f'not-{fact_names}', fact_args
        elif expr.node_type == OperatorKind.PARAM_EXP:
            return '', [expr]
        else:
            assert False, f"Unexpected node type: {expr.node_type}"