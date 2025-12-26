import os
import unified_planning as up

from copy import deepcopy
from unified_planning.io import PDDLReader, PDDLWriter
from unified_planning.shortcuts import Compiler, CompilationKind, OneshotPlanner

from storytelling_bspace_dims.possible_endings import PossibleEndingsSMT
from up_behaviour_planning.FBIPlannerUp import FBIPlanner

from utilities import get_story_domain, generate_stories

env = up.environment.get_environment()
env.error_used_name = False
env.factory.add_engine('FBIPlanner', __name__, 'FBIPlanner')

pddl_dir = os.path.join(os.path.dirname(__file__), '..', 'pddl-domains')
domain = os.path.join(pddl_dir, 'aladdin-npc', 'domain.pddl')
problem = os.path.join(pddl_dir, 'aladdin-npc', 'problem.pddl')

task = PDDLReader().parse_problem(domain, problem)

compilationlist  = [['intention_remover', CompilationKind.INTENTIONAL_REMOVING]]
compilationlist += [["up_conditional_effects_remover", CompilationKind.CONDITIONAL_EFFECTS_REMOVING]]

names = [name for name, _ in compilationlist]
compilationkinds = [kind for _, kind in compilationlist]
with Compiler(names=names, compilation_kinds=compilationkinds) as compiler:
    compiled_task = compiler.compile(task)

planner_params = {
  "fbi-planner-type": "ForbidBehaviourIterativeSMT",
  "base-planner-cfg": {
    # "planner-name": "symk-opt",
    # "symk_search_time_limit": "900s",
    "k": 5 # The number of plans to be generated # generate all behaviours.
  },
  "bspace-cfg": {
    "use_fixed_length_formula": True,
    'horizon-planning': True,
    'skip-actions': False,
    "disable-after-goal-state-actions": True,
    "upper-bound": 12,
    'quality-bound-factor': 1.0,
    "solver-timeout-ms": 60000,
    "solver-memorylimit-mb": 16000,
    "dims": [[PossibleEndingsSMT, None]],
    "compliation-list": [
        ["up_quantifiers_remover", "QUANTIFIERS_REMOVING"],
        ["up_disjunctive_conditions_remover", "DISJUNCTIVE_CONDITIONS_REMOVING"],
        ["up_grounder", "GROUNDING"]
    ],
    "run-plan-validation": False,    
  }
}


with OneshotPlanner(name='FBIPlanner',  params=deepcopy(planner_params)) as planner:
  result = planner.solve(compiled_task.problem)


pass








problems = get_story_domain('aladdin')

predicates  = []
# predicates += ['has']
# predicates += ['alive']
# predicates += ['became_a_theif']
predicates += [('(married-to ? jasmine)', 'Atleast', 1)]
# predicates += [('(married Jasmine ?)', 'Atleast', 1)]
# predicates += [('(in-prison ?)', 'Atleast', 1)]
predicates += [('(controls ? gene)', 'Atleast', 1)]

dims  = []
# dims += 
# dims += [[UtilityValueSMT, {}]]
# dims += [[UtilitySetSMT, {}]]
# dims += [[GoalPredicatesOrderingSMT, None]]
compilationlist = []

# compilationlist += [["fast-downward-reachability-grounder", "GROUNDING"]]


sandboxdir = os.path.join(os.path.dirname(__file__), 'sandbox')
# os.makedirs(sandboxdir, exist_ok=True)
domain = os.path.join(sandboxdir, 'grounded-compiled-domain.pddl')
problem = os.path.join(sandboxdir, 'grounded-compiled-problem.pddl')

plans, log = generate_stories(domain, problem, planner_params, True)

# plans, log = generate_stories(problems[0][1], problems[0][2], planner_params, True)

pass



# # 1. Construct the planner's parameters:
# # - define the behaviour space's dimensions 

# # dims += [(GoalPredicatesOrderingSMT, None)]
# # dims += [(MakespanOptimalCostSMT, {"cost-bound-factor": 2.0})]
# dims += [(FunctionsSMT, resource)]




# Plan 0 
# ('jail(the_sultan, jafar)\ncollect(aladdin, genie_lamp, palace_of_agrabah)\nsummon(aladdin, genie)\ncast-spell(aladdin, fall-in-love-spell, jasmine)\npropose(jasmine, aladdin)\nmarry(aladdin, jasmine)', 
#  '(married_aladdin_jasmine_6 == True) ^ (in-prison_jafar_6 == True)')

# Plan 1
# ('collect(aladdin, genie_lamp, palace_of_agrabah)\nsummon(aladdin, genie)\njail(jafar, the_sultan)\ncast-spell(aladdin, fall-in-love-spell, jasmine)\npropose(jasmine, aladdin)\nmarry(aladdin, jasmine)', 
#  '(married_aladdin_jasmine_6 == True) ^ (in-prison_the_sultan_6 == True)')

# Plan 2
# ('collect(jafar, genie_lamp, palace_of_agrabah)\njail(jafar, the_sultan)\nsummon(jafar, genie)\ncast-spell(jafar, fall-in-love-spell, jasmine)\npropose(jasmine, jafar)\nmarry(jafar, jasmine)', 
#  '(married_jafar_jasmine_6 == True) ^ (in-prison_the_sultan_6 == True)')

# Plan 3
#  ('jail(the_sultan, aladdin)\ncollect(jafar, genie_lamp, palace_of_agrabah)\nsummon(jafar, genie)\ncast-spell(jafar, fall-in-love-spell, jasmine)\npropose(jasmine, jafar)\nmarry(jafar, jasmine)', 
#   '(married_jafar_jasmine_6 == True) ^ (in-prison_aladdin_6 == True)')

# Plan 4
# ('collect(jasmine, genie_lamp, palace_of_agrabah)\nsummon(jasmine, genie)\ncast-spell(jasmine, fall-in-love-spell, jafar)\npropose(jafar, jasmine)\nmarry(jafar, jasmine)\njail(the_sultan, jafar)', 
#  '(married_jafar_jasmine_6 == True) ^ (in-prison_jafar_6 == True)')
