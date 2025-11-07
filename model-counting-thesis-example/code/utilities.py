import os
import sys
import subprocess

from subprocess import SubprocessError


from unified_planning.io import PDDLReader, PDDLWriter

from unified_planning.shortcuts import CompilationKind
from behaviour_planning.over_domain_models.smt.fbi.planner.planner import ForbidBehaviourIterativeSMT
from behaviour_planning.over_domain_models.smt.bss.behaviour_count.behaviour_count import BehaviourCountSMT

from behaviour_planning_asp.compilers.asp_encoder import ASPEncoder
from behaviour_planning_asp.compilers.delete_then_set_remover import DeleteThenSetRemover
from behaviour_planning_asp.compilers.renamer import Renamer

def fi_generated_plans(task, domainfile, problemfile, dims, sandbox_dir, k=1000, q=1.0):
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
    cmd += [str(k)]
    cmd += ["--quality-bound"]
    cmd += [str(q)]
    cmd += ["--symmetries"]
    cmd += ["--use-local-folder"]
    cmd += ["--clean-local-folder"]
    cmd += ["--suppress-planners-output"]
    cmd += ["--overall-time-limit"]
    cmd += ["3600"]

    tmprun = os.path.join(sandbox_dir, 'sandbox-fi-run-tmp', os.path.basename(os.path.dirname(domainfile)), os.path.basename(os.path.dirname(problemfile)))
    tmpdir = os.path.join(sandbox_dir, 'sandbox-fi-tmpdir',  os.path.basename(os.path.dirname(domainfile)), os.path.basename(os.path.dirname(problemfile)))
    tmpscoredir = os.path.join(sandbox_dir, 'sandbox-fi-score-tmpdir', os.path.basename(os.path.dirname(domainfile)), os.path.basename(os.path.dirname(problemfile)))
    os.makedirs(tmprun, exist_ok=True)
    os.makedirs(tmpdir, exist_ok=True)
    os.makedirs(tmpscoredir, exist_ok=True)

    # /Users/mustafafaisal/Developer/behaviour-planning-case-studies/model-counting-thesis-example/code/sandbox/sandbox-fi-tmpdir/rovers/rovers/found_plans/done
    # /Users/mustafafaisal/Developer/behaviour-planning-case-studies/model-counting-thesis-example/code/sandbox/sandbox-fi-run-tmp/rovers/rovers/found_plans/done

    fienv = os.environ.copy()
    fienv['FI_PLANNER_RUNS'] = tmprun
    try:
        output = subprocess.check_output(cmd, env=fienv, cwd=tmprun)
        pass
    except SubprocessError as e:
        pass

    planlist = set()
    found_plans = os.path.join(tmprun, 'found_plans', 'done')
    if not os.path.exists(found_plans): return []
    for plan in os.listdir(found_plans):
        with open(os.path.join(found_plans, plan), 'r') as f:
            plan = f.read()
            if not plan in planlist: planlist.add(plan)

    bs_cfg = {
        "fbi-planner-type": "ForbidBehaviourIterativeSMT",
        "base-planner-cfg": {
            "planner-name": "symk-opt",
            "symk_search_time_limit": "900s"
        },
        "bspace-cfg": {
            'ignore-seed-plan': False,
            'quality-bound-factor': q,
            "solver-timeout-ms": 60000 * 5,
            "solver-memorylimit-mb": 16000,
            "dims": dims,
            "compliation-list": [
                ["up_quantifiers_remover", CompilationKind.QUANTIFIERS_REMOVING],
                ["fast-downward-reachability-grounder", CompilationKind.GROUNDING]
            ],
            "run-plan-validation": False,
            "behaviours-only": False
        },
        'dims': dims
    }

    bc_counter = BehaviourCountSMT(domainfile, problemfile, bs_cfg, list(planlist), is_oversubscription_planning=False)
    selected_plans = bc_counter.selected_plans(k)
    # now we need to lift this plan
    return [plan.replace_action_instances(bc_counter.gr_result.map_back_action_instance) for plan in selected_plans]

def fbi_smt_generated_plans(task, domainfile, problemfile, dims, sandbox_dir, k=1000, q=1.0):
    _cfg = {
        "fbi-planner-type": "ForbidBehaviourIterativeSMT",
        "base-planner-cfg": {
            "planner-name": "symk-opt",
            "symk_search_time_limit": "900s"
        },
        "bspace-cfg": {
            'ignore-seed-plan': False,
            'quality-bound-factor': q,
            "solver-timeout-ms": 60000 * 5,
            "solver-memorylimit-mb": 16000,
            "dims": dims,
            "compliation-list": [
                ["up_quantifiers_remover", CompilationKind.QUANTIFIERS_REMOVING],
                ["fast-downward-reachability-grounder", CompilationKind.GROUNDING]
            ],
            "run-plan-validation": False,
            "behaviours-only": False
        }
    }
    
    fbi_planner = ForbidBehaviourIterativeSMT(task, _cfg['bspace-cfg'], _cfg['base-planner-cfg'])
    plans = fbi_planner.plan(k) # limit for 100 behaviours for now.
    return plans

def compile_to_asp(task):
    removed_delete_then_task = DeleteThenSetRemover().compile(task).problem
    renamed_task = Renamer().compile(removed_delete_then_task).problem
    return ASPEncoder().compile(renamed_task)

def stringify_plans(task, plans):
    task_writer = PDDLWriter(task)
    return [task_writer.get_plan(p).replace('-', '_') for p in plans]