import os
import up_symk
import unified_planning as up
from unified_planning.io import PDDLReader, PDDLWriter
from unified_planning.shortcuts import OneshotPlanner, Compiler, CompilationKind
import unified_planning.engines.results as UPResults

from pypmt.apis import solveUP


pddl_dir = os.path.join(os.path.dirname(__file__), '..', 'pddl-domains')

# domain = os.path.join(pddl_dir, 'robin-hood-mine', 'domain.pddl')
# problem = os.path.join(pddl_dir, 'robin-hood-mine', 'problem.pddl')

# domain = os.path.join(pddl_dir, 'aladdin-npc', 'domain.pddl')
# problem = os.path.join(pddl_dir, 'aladdin-npc', 'problem.pddl')


# domain = os.path.join(pddl_dir, 'Knives-Out', 'domain.pddl')
# problem = os.path.join(pddl_dir, 'Knives-Out', 'problem.pddl')

domain = os.path.join(pddl_dir, 'aladdin-npc', 'domain.pddl')
problem = os.path.join(pddl_dir, 'aladdin-npc', 'problem.pddl')

env = up.environment.get_environment()
env.error_used_name = False


task = PDDLReader().parse_problem(domain, problem)

if True:

    compilationlist  = [['intention_remover', CompilationKind.INTENTIONAL_REMOVING]]
    compilationlist += [['up_conditional_effects_remover', CompilationKind.CONDITIONAL_EFFECTS_REMOVING]]

    names = [name for name, _ in compilationlist]
    compilationkinds = [kind for _, kind in compilationlist]
    with Compiler(names=names, compilation_kinds=compilationkinds) as compiler:
        compiled_task = compiler.compile(task)

    pddl_writer = PDDLWriter(compiled_task.problem)

    # write the compiled domain and problem to a single file for debugging later.
    with open(f'sandbox-{compiled_task.problem.name}-compiled.pddl', 'w') as f:
        f.write(pddl_writer.get_domain())
        f.write('\n')
        f.write(pddl_writer.get_problem())

pass

# sol = solveUP(compiled_task.problem, "seq")

# A generated plan:
# (pick-because-character-intends-alive-0 bob gun bob-home)
# (travel-because-character-intends-has bob bob-home downtown)
# (kill-because-murderer-intends-has bob alice gun downtown)
# (find-clue-because-police-intends-has sherlock gun bob downtown)
# (arrest-because-arrester-intends-alive sherlock bob bob-home downtown)


pass

with OneshotPlanner(name="symk-opt",  
                    params={"symk_search_time_limit": "900s",}) as planner:
    result   = planner.solve(compiled_task.problem)
    seedplan = result.plan if result.status in UPResults.POSITIVE_OUTCOMES else None

pass


# Generated plan:
# fall_in_love(aladdin, jasmine, castle)
# travel_because_traveller_intends_married_to(aladdin, castle, mountain, aladdin, jasmine)
# slay_because_slayer_intends_married_to(aladdin, dragon, mountain, aladdin, jasmine)
# pillage_because_pillager_intends_married_to(aladdin, dragon, lamp, mountain, aladdin, jasmine)
# summon_because_who_intends_married_to(aladdin, gene, lamp, mountain, aladdin, jasmine)
# fall_in_love(jafar, jasmine, castle)
# command_at_because_intends_married_to(aladdin, gene, lamp, aladdin, castle, aladdin, jasmine)
# love_spell_because_gen_intends_at(gene, jasmine, jafar, aladdin, castle)
# marry_because_bride_intends_married_to(jafar, jasmine, castle, jasmine, jafar)
# slay_because_slayer_intends_married_to(aladdin, gene, mountain, aladdin, jasmine)

# # compare domains.
# original_domain = '/Users/mustafafaisal/Desktop/npc/ex-story-jtc.pddl'
# original_problem = '/Users/mustafafaisal/Desktop/npc/ex-story-1.pddl'
# task_original = PDDLReader().parse_problem(original_domain, original_problem)

pass