import argparse
import os
import sys
import json
import time

import unified_planning as up
import subprocess
import tempfile

from itertools import chain
from subprocess import SubprocessError
from copy import deepcopy
from unified_planning.io import PDDLReader, PDDLWriter
from unified_planning.shortcuts import CompilationKind, Compiler
from unified_planning.shortcuts import OneshotPlanner, AnytimePlanner, OperatorKind
from unified_planning.engines import PlanGenerationResultStatus as ResultsStatus

from behaviour_planning.over_domain_models.smt.shortcuts import GoalPredicatesOrderingSMT, MakespanOptimalCostSMT, ResourceCountSMT, UtilityValueSMT, FunctionsSMT
from behaviour_planning.over_domain_models.smt.shortcuts import ForbidBehaviourIterativeSMT

from behaviour_planning.over_domain_models.smt.bss.behaviour_count.behaviour_counter_simulator import BehaviourCountSimulator

from storytelling_bspace_dims.possible_endings import PossibleEndingsSMT, PossibleEndingsSimulator

from behaviour_planning.over_domain_models.smt.fbi.planner.planner import ForbidBehaviourIterativeSMT


def arg_parser():
    parser = argparse.ArgumentParser(description="Generate SLURM tasks for running experiments.")
    parser.add_argument('--taskfile', type=str, required=True, help='Path to the task file.')
    parser.add_argument('--outputdir', type=str, required=True, help='Directory to store output files.')
    return parser

def compile_qunatifiers_task(task):
    from unified_planning.shortcuts import Compiler, CompilationKind
    compilationlist  = []
    compilationlist += [["up_quantifiers_remover", CompilationKind.QUANTIFIERS_REMOVING]]
    compilationlist += [['up_conditional_effects_remover', CompilationKind.CONDITIONAL_EFFECTS_REMOVING]]
    compilationlist += [['up_grounder', CompilationKind.GROUNDING]]
    names = [name for name, _ in compilationlist]
    compilationkinds = [kind for _, kind in compilationlist]
    with Compiler(names=names, compilation_kinds=compilationkinds) as compiler:
        compiled_task = compiler.compile(task)
    return compiled_task.problem

def compile_end_story_action_task(task):
    import unified_planning as up
    from collections import OrderedDict    
    from unified_planning.model import InstantaneousAction
    from unified_planning.model.walkers.dnf import Dnf
    from pypmt.encoders.utilities import str_repr

    new_task = task.clone()
    end_story_fluent = list(filter(lambda f: f.name == 'the-end', new_task.fluents)).pop()
    assert len(task.goals) == 1, "Task must have a single goal"
    for goal in task.goals:
        for dnf_expr in Dnf(new_task.environment).get_dnf_expression(goal).args:
            if dnf_expr.is_fluent_exp():
                base_name =  f'end_story_{str_repr(dnf_expr)}'
            else:
                base_name = f'end_story_{"_and_".join(map(lambda a: str_repr(a), map(lambda a: a.args[0] if a.is_not() else a, dnf_expr.args)))}'
            _compiled_action = InstantaneousAction(base_name, OrderedDict(), new_task.environment)
            _compiled_action.add_precondition(dnf_expr)
            _compiled_action.add_effect(end_story_fluent, True)
            new_task.add_action(_compiled_action)

    new_task.clear_goals()
    new_task.add_goal(new_task.environment.expression_manager.FluentExp(end_story_fluent))
    return new_task


def construct_task_details_info(taskdetails):
    return {
            'domain' : os.path.basename(os.path.dirname(taskdetails['domainfile'])) + '/' + os.path.basename(taskdetails['domainfile']),
            'problem': os.path.basename(taskdetails['problemfile']),
            'planner': taskdetails['planner'],
            'tag' : taskdetails['planner'],
            'planning-type': taskdetails['planning-type'],
            'k': taskdetails['k-plans'],
            'q': taskdetails['q']
        }


def construct_results_file(taskdetails, task, plans):
    task_writer = PDDLWriter(task)
    resultsfile = {
        'plans': [task_writer.get_plan(p) + f';{len(p.actions)} cost (unit)' + f'\n;behaviour: {p.behaviour.replace("\n","")}' for p in plans],
        'diversity-scores': {
            'behaviour-count': len(set(p.behaviour for p in plans))
        },
        'info' : construct_task_details_info(taskdetails),
    }
    return resultsfile

def select_plans_using_bspace_simulator(taskdetails, task, dims, planslist):
    from behaviour_planning.over_domain_models.smt.bss.behaviour_count.behaviour_counter_simulator import BehaviourCountSimulator
    bspace = BehaviourCountSimulator(task, planslist, dims)
    return bspace, bspace.selected_plans(taskdetails['k-plans'])

def run_fbi(taskdetails, dims, compilation_list):
    pass

def run_symk(taskdetails, dims, compilation_list):
    pass


def run_fi(taskdetails):
    tmpdir = os.path.join(taskdetails['sandbox-dir'], 'tmp', taskdetails['filename'].replace('.json',''))
    os.makedirs(tmpdir, exist_ok=True)
    
    with tempfile.TemporaryDirectory(dir=tmpdir) as tmpdirname:
        task = compile_qunatifiers_task(PDDLReader().parse_problem(taskdetails['domainfile'], taskdetails['problemfile']))
        new_task = compile_end_story_action_task(task)
        pddl_writer = PDDLWriter(new_task)
        # write the compiled domain and problem to a single file for debugging later.
        domainfile = os.path.join(tmpdir, 'domain.pddl')
        with open(domainfile, 'w') as f:
            f.write(pddl_writer.get_domain())
        problemfile = os.path.join(tmpdir, 'problem.pddl')
        with open(problemfile, 'w') as f:
            f.write(pddl_writer.get_problem())

        cmd  = [sys.executable]
        cmd += ["-m"]
        cmd += ["forbiditerative.plan"]
        cmd += ["--planner"]
        cmd += ["extended_unordered_topq"]
        cmd += ["--domain"]
        cmd += [domainfile]
        cmd += ["--problem"]
        cmd += [problemfile]
        cmd += ["--number-of-plans"]
        cmd += [str(taskdetails['k-plans'])]
        cmd += ["--quality-bound"]
        cmd += [str(taskdetails['q'])]
        cmd += ["--symmetries"]
        cmd += ["--use-local-folder"]
        cmd += ["--clean-local-folder"]
        cmd += ["--suppress-planners-output"]
        cmd += ["--overall-time-limit"]
        cmd += ["5400"]

        fienv = os.environ.copy()
        fienv['FI_PLANNER_RUNS'] = tmpdir
        logs = []
        try:
            output = subprocess.check_output(cmd, env=fienv, cwd=tmpdir)
        except SubprocessError as e:
            logs.append(str(e))
        finally:    
            planlist = []
            found_plans = os.path.join(tmpdir, 'found_plans', 'done')
            if not os.path.exists(found_plans): return {}
            for plan in os.listdir(found_plans):
                with open(os.path.join(found_plans, plan), 'r') as f:
                    plan = f.read()
                    if not plan in planlist: planlist.append(plan)
            planlist = set(planlist)
            read_task = PDDLReader().parse_problem(domainfile, problemfile)
            generated_results = os.path.join(taskdetails['sandbox-dir'], 'fi-solved-instances')
            os.makedirs(generated_results, exist_ok=True)
            planlist = list(map(lambda p: PDDLReader().parse_plan_string(read_task, p), list(set(planlist))))

            from unified_planning.model.walkers.free_vars import FreeVarsExtractor
            vars = list(map(lambda expr: FreeVarsExtractor().get(expr), task.goals))
            vars = [elem for s in vars for elem in s]

            # map the variables from task to read_task.
            _is_same = lambda a, b: a._content.payload.name.replace('-', '_') == b._content.payload.name.replace('-', '_')
            dims = [
                [PossibleEndingsSimulator, [f for f in read_task.initial_values.keys() if any(_is_same(f, var) for var in vars)]]
            ]

            bspace, selected_plans = select_plans_using_bspace_simulator(taskdetails, read_task, dims, planlist)
            results = construct_results_file(taskdetails, read_task, selected_plans)
            return results

def solve(taskname, args):

    env = up.environment.get_environment()
    env.error_used_name = False
    env.credits_stream  = None

    with open(args.taskfile, 'r') as f:
        taskdetails = json.load(f)
    
    # TODO: Run a task renamer compilation to avoid the issue triggered by the mismatch between action names due 
    # the difference in - and _.
    tmpdir = os.path.join(taskdetails['sandbox-dir'], 'tmp', taskdetails['filename'].replace('.json',''))
    os.makedirs(tmpdir, exist_ok=True)
    
    dims = []
    
    ret_details = {}
    start_time = time.time()
    match taskdetails['planner']:
        case 'fbi-smt-naive' | 'fbi-smt':
            ret_details = run_fbi(taskdetails)
        case 'fi-bc':
            ret_details = run_fi(taskdetails)
        case 'symk':
            ret_details = run_symk(taskdetails)
        case _:
            assert False, f"Unknown planning type {taskdetails['planning-type']}"
    end_time = time.time()
    ret_details['total-time-seconds'] = end_time - start_time

    os.makedirs(os.path.dirname(args.outputdir), exist_ok=True)
    outputpath = os.path.join(args.outputdir, f'{taskname}-results.json')
    if len(ret_details) == 0: return
    with open(outputpath, 'w') as f:
        json.dump(ret_details, f, indent=4)
    
    # delete created files.
    if os.path.exists(taskdetails['domainfile']):
        # delete the dir 
        import shutil
        shutil.rmtree(os.path.dirname(taskdetails['domainfile']))

def main():
    args = arg_parser().parse_args()
    sandbox_dir = os.path.dirname(args.outputdir)
    taskname = os.path.basename(args.taskfile).replace('.json','')
    errorsdir = os.path.join(sandbox_dir, 'errors')
    os.makedirs(errorsdir, exist_ok=True)
    os.makedirs(args.outputdir, exist_ok=True)
    
    # # for dev only
    solve(taskname, args)

    try:
        solve(taskname, args)
    except Exception as e:
        with open(os.path.join(errorsdir, f'{taskname}_error.log'), 'a') as f:
            f.write(str(e) + '\n')
    
    pass

if __name__ == "__main__":
    main()