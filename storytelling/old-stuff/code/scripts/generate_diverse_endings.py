import sys
import json
import cProfile
import os
from copy import deepcopy
from collections import OrderedDict
import time

import subprocess
from subprocess import SubprocessError
import tempfile
import unified_planning as up
from unified_planning.io import PDDLWriter, PDDLReader
from unified_planning.engines import PlanGenerationResultStatus as ResultsStatus
from unified_planning.shortcuts import OneshotPlanner, CompilationKind, SequentialSimulator, AnytimePlanner

from unified_planning.model import InstantaneousAction

from up_behaviour_planning.FBIPlannerUp import FBIPlanner


from utilities import getkeyvalue, prepare_results_dump, create_parser, get_profiling_dumpfile, compile_intention_task, compile_qunatifiers_task, compile_end_story_action_task, get_planner_configuration

def maxsum_selection(domainfile, problemfile, found_plans, plans_count, k, tmpscoredir):
    maxsum_selected_plans = []
    ibmexe = os.path.join(os.path.dirname(__file__), '..', 'ibm-diversescore', 'fast-downward.py')
    metric = 'stability'
    score  = f"subset(compute_{metric.lower()}_metric=true,aggregator_metric=avg,plans_as_multisets=false,plans_subset_size={k},exact_method=false,similarity=false,reduce_labels=false,dump_plans=true)"
    cmd = [sys.executable, 
        ibmexe, 
        domainfile, 
        problemfile, 
        "--diversity-score", score, 
        "--internal-plan-files-path", found_plans, 
        "--internal-num-plans-to-read", str(plans_count)]
    result = subprocess.check_output(cmd, universal_newlines=True, cwd=tmpscoredir)
    for plan in os.listdir(tmpscoredir):
        with open(os.path.join(tmpscoredir, plan), 'r') as f:
            maxsum_selected_plans.append(f.read())
    return maxsum_selected_plans    

def bc_selection(planlist, k):
    pass

def simulate_plan(task, plan):
    states = []
    with SequentialSimulator(problem=task) as simulator:
        initial_state = simulator.get_initial_state()
        current_state = initial_state
        states += [current_state]
        for action_instance in plan.actions:
            current_state = simulator.apply(current_state, action_instance)
            if current_state is None:
                assert False, "No cost available since the plan is invalid."
            states.append(current_state)
    return states


def FBIPlannerWrapper(args, task, plannercfg):
    import up_symk
    from math import ceil
    env = up.environment.get_environment()
    env.error_used_name = False
    env.factory.add_engine('FBIPlanner', __name__, 'FBIPlanner')
    # get FBI's configuration.
    planner_configuration = get_planner_configuration(args, task)
    # let's solve this task using symk first to know the bound and then extend it
    # with a factor of 100%.
    with OneshotPlanner(name='symk-opt', params={"symk_search_time_limit": "900s"}) as planner:
        result = planner.solve(task)
        if not (result.status in up.engines.results.POSITIVE_OUTCOMES): return [], []
        planner_configuration['planner-parameters']['bspace-cfg']['upper-bound'] = int(ceil(len(result.plan.actions) * args.quality_bound))
            
    with OneshotPlanner(name='FBIPlanner', params=planner_configuration['planner-parameters']) as planner:
        result = planner.solve(task)
    planlist = [] if len(result[0]) < 1 else [r.plan for r in result[0]]
    planlist = list(filter(lambda p: not p is None, planlist))
    return list(map(lambda p: p if isinstance(p, str) else f'{PDDLWriter(task).get_plan(p)}; {len(p.actions)} cost (unit)', planlist)), list(map(lambda p: p.behaviour, planlist)) 

def FIPlannerWrapper(args, task, plannercfg):
    from unified_planning.model.walkers.free_vars import FreeVarsExtractor
    vars = list(map(lambda expr: FreeVarsExtractor().get(expr), task.goals))
    vars = [elem for s in vars for elem in s]

    # Write the compiled task into the tmp-run dir.
    sandboxdirname = 'non-intentional' if not args.compile_intention else 'intentional'
    current_prj_dir = os.path.join(os.path.dirname(__file__), '..', f'sandbox-{sandboxdirname}')

    tmprun = os.path.join(current_prj_dir, 'sandbox-fi-run-tmp', f'{plannercfg["tag"]}-{task.name}-{args.k_plans}')
    tmpdir = os.path.join(current_prj_dir, 'sandbox-fi-tmpdir',  f'{plannercfg["tag"]}-{task.name}-{args.k_plans}')
    tmpscoredir = os.path.join(current_prj_dir, 'sandbox-fi-score-tmpdir',  f'{plannercfg["tag"]}-{task.name}-{args.k_plans}-score')
    os.makedirs(tmprun, exist_ok=True)
    os.makedirs(tmpdir, exist_ok=True)
    os.makedirs(tmpscoredir, exist_ok=True)

    # here we need to recompile the task, such that the end_story action is re-generated based on
    # the preconditions.
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
    cmd += [str(args.k_plans)]
    # cmd += ["1000"]
    cmd += ["--quality-bound"]
    cmd += [str(args.quality_bound)]
    cmd += ["--symmetries"]
    cmd += ["--use-local-folder"]
    cmd += ["--clean-local-folder"]
    cmd += ["--suppress-planners-output"]
    cmd += ["--overall-time-limit"]
    cmd += ["3600"]

    fienv = os.environ.copy()
    fienv['FI_PLANNER_RUNS'] = tmprun
    try:
        output = subprocess.check_output(cmd, env=fienv, cwd=tmpdir)
    except SubprocessError as e:
        print(e)

    planlist = []
    found_plans = os.path.join(tmpdir, 'found_plans', 'done')
    if not os.path.exists(found_plans): return [], []
    for plan in os.listdir(found_plans):
        with open(os.path.join(found_plans, plan), 'r') as f:
            plan = f.read()
            if not plan in planlist: planlist.append(plan)
    
    selection_method = getkeyvalue(plannercfg, 'selection-method')
    optimise_bc = False
    match selection_method:
        case 'maxsum':
            if len(planlist) > args.k_plans: 
                planlist = maxsum_selection(domainfile, problemfile, found_plans, len(planlist), args.k_plans, tmpscoredir) 
        case 'k':
            planlist = planlist[:args.k_plans] if len(planlist) > args.k_plans else planlist
        case 'bc':
            optimise_bc = True # we will simulate the plans later and then optimise on the behaviour count.
        case _:
            assert False, "Unknown selection method"

    # read the plans as up.
    solved_task = PDDLReader().parse_problem(domainfile, problemfile)
    planlist = list(map(lambda p: PDDLReader().parse_plan_string(solved_task, p), planlist))

    # simulate the generated plans.
    planbehaviour_map = []
    for i, plan in enumerate(planlist):
        if optimise_bc and len(set(map(lambda e:e[1], planbehaviour_map))) >= args.k_plans: break
        end_state = simulate_plan(solved_task, plan)[-1]
        vars_value = []
        for v in vars:
            try:
                vars_value.append(f'{str(v)} == {str(end_state.get_value(v))}')
            except:
                vars_value.append(f'{str(v)} == false')
        planbehaviour_map += [(plan, ' ^ '.join(vars_value))]

    return list(map(lambda p: p if isinstance(p, str) else f'{PDDLWriter(solved_task).get_plan(p)}; {len(p.actions)} cost (unit)', map(lambda e:e[0], planbehaviour_map))), list(map(lambda e:e[1], planbehaviour_map))


def SYMKPlannerWrapper(args, task, plannercfg):

    import up_symk
    from unified_planning.model.walkers.free_vars import FreeVarsExtractor
    vars = list(map(lambda expr: FreeVarsExtractor().get(expr), task.goals))
    vars = [elem for s in vars for elem in s]

    planlist = []
    search_config = f"symq-bd(plan_selection=top_k(num_plans={args.k_plans},dump_plans=true),quality={args.quality_bound})"
    with AnytimePlanner(name='symk-opt', params={"symk_anytime_search_config": search_config, "symk_search_time_limit": "3600s"}) as planner:
        for i, result in enumerate(planner.get_solutions(task)):
            if result.status == ResultsStatus.INTERMEDIATE:
                planlist.append(result.plan) if i < args.k_plans else None
    
    planbehaviour_map = []
    for i, plan in enumerate(planlist):
        end_state = simulate_plan(task, plan)[-1]
        vars_value = []
        for v in vars:
            try:
                vars_value.append(f'{str(v)} == {str(end_state.get_value(v))}')
            except:
                vars_value.append(f'{str(v)} == false')
        planbehaviour_map += [(plan, ' ^ '.join(vars_value))]
    return list(map(lambda p: p if isinstance(p, str) else f'{PDDLWriter(task).get_plan(p)}; {len(p.actions)} cost (unit)', planlist)), list(map(lambda e:e[1], planbehaviour_map))



def main(args):

    task = PDDLReader().parse_problem(args.domain, args.problem)

    with open(args.planner, 'r') as f:
        planner = json.load(f)
    
    if args.compile_intention: task = compile_intention_task(task)

    task = compile_qunatifiers_task(task)

    planlist = []
    behaviourlist = []
    start_time = time.time()
    match planner['planner']:
        case 'fi':
            planlist, behaviourlist = FIPlannerWrapper(args, task, planner)
        case 'fbismt':
            planlist, behaviourlist = FBIPlannerWrapper(args, task, planner)
        case 'symk':
            planlist, behaviourlist = SYMKPlannerWrapper(args, task, planner)
    end_time = time.time()

    if len(planlist) < args.k_plans: return # skip unsolved problems.
    with open(args.output, 'w') as f:
        json.dump(prepare_results_dump(args, planlist, behaviourlist, task, planner, end_time-start_time), f, indent=4)

if __name__ == '__main__':
    # For debugging only
    main(create_parser().parse_args(sys.argv[1:]))
    pass
    # try:
    #     args = create_parser().parse_args(sys.argv[1:])
    #     profilingfile = get_profiling_dumpfile(args)
    #     cProfile.runctx('main(args)', {'args':args, 'main': main}, {}, filename=profilingfile)
    # except Exception as e:
    #     print(e)
    #     sys.exit(1)