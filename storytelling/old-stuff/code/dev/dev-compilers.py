import os
import unified_planning as up
from unified_planning.io import PDDLReader, PDDLWriter
from unified_planning.shortcuts import Compiler, CompilationKind

env = up.environment.get_environment()
env.error_used_name = False


domain  = '/Users/mustafafaisal/Desktop/npc/ex-story.npddl'
problem = '/Users/mustafafaisal/Desktop/npc/ex-story-1.pddl'

task = PDDLReader().parse_problem(domain, problem)

compilationlist = []
compilationlist += [['intention_remover', CompilationKind.INTENTIONAL_REMOVING]]

names = [name for name, _ in compilationlist]
compilationkinds = [kind for _, kind in compilationlist]
with Compiler(names=names, compilation_kinds=compilationkinds) as compiler:
    compiled_task = compiler.compile(task)

sandboxdir = os.path.join(os.path.dirname(__file__), 'sandbox')
os.makedirs(sandboxdir, exist_ok=True)

PDDLWriter(compiled_task.problem).write_domain(os.path.join(sandboxdir, 'compiled-domain.pddl'))
PDDLWriter(compiled_task.problem).write_problem(os.path.join(sandboxdir, 'compiled-problem.pddl'))

compilationlist = [["up_quantifiers_remover", CompilationKind.QUANTIFIERS_REMOVING]]
# compilationlist += [["fast-downward-reachability-grounder", CompilationKind.GROUNDING]]
compilationlist += [["up_grounder", CompilationKind.GROUNDING]]
names = [name for name, _ in compilationlist]
compilationkinds = [kind for _, kind in compilationlist]
with Compiler(names=names, compilation_kinds=compilationkinds) as compiler:
    compiled_task_2 = compiler.compile(compiled_task.problem)


PDDLWriter(compiled_task_2.problem).write_domain(os.path.join(sandboxdir, 'grounded-compiled-domain.pddl'))
PDDLWriter(compiled_task_2.problem).write_problem(os.path.join(sandboxdir, 'grounded-compiled-problem.pddl'))

import up_symk

pass