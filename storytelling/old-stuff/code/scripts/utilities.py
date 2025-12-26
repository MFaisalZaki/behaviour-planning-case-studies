import os
import argparse
import importlib.util
from copy import deepcopy
from collections import defaultdict
from unified_planning.io import PDDLWriter, PDDLReader

def prepare_results_dump(args, planlist, behaviourlist, task, planner, time_taken):
    results = deepcopy(planner)
    results['story'] = task.name
    results['domain'] = args.domain
    results['problem'] = args.problem
    results['k'] = args.k_plans
    results['q'] = args.quality_bound
    results['plans'] = planlist
    results['behaviour-count'] = len(set(behaviourlist))
    results['behaviours'] = behaviourlist
    results['time-taken'] = time_taken
    return results

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


def construct_behaviour_space(args, planner_config, task):
    dimensions = []
    for dim in getkeyvalue(planner_config, 'dims'):
        match dim[0]:
            case 'PossibleEndingsSMT':
                from storytelling_bspace_dims.possible_endings import PossibleEndingsSMT
                dimensions.append([PossibleEndingsSMT, task.goals])
            case _:
                raise NotImplementedError(f"Dimension {dim[0]} is not implemented")
    return dimensions

def compile_intention_task(task):
    from unified_planning.io import PDDLReader, PDDLWriter
    from unified_planning.shortcuts import Compiler, CompilationKind

    compilationlist  = [['intention_remover', CompilationKind.INTENTIONAL_REMOVING]]
    # compilationlist += [['up_conditional_effects_remover', CompilationKind.CONDITIONAL_EFFECTS_REMOVING]]
    # compilationlist += [["up_quantifiers_remover", CompilationKind.QUANTIFIERS_REMOVING]]
    names = [name for name, _ in compilationlist]
    compilationkinds = [kind for _, kind in compilationlist]
    with Compiler(names=names, compilation_kinds=compilationkinds) as compiler:
        compiled_task = compiler.compile(task)
    
    return compiled_task.problem

def compile_qunatifiers_task(task):
    from unified_planning.shortcuts import Compiler, CompilationKind
    compilationlist  = []
    compilationlist += [["up_quantifiers_remover", CompilationKind.QUANTIFIERS_REMOVING]]
    compilationlist += [['up_conditional_effects_remover', CompilationKind.CONDITIONAL_EFFECTS_REMOVING]]
    names = [name for name, _ in compilationlist]
    compilationkinds = [kind for _, kind in compilationlist]
    with Compiler(names=names, compilation_kinds=compilationkinds) as compiler:
        compiled_task = compiler.compile(task)
    return compiled_task.problem

def get_planner_configuration(args, task):
    import json
    from unified_planning.shortcuts import CompilationKind
    import os
    assert os.path.exists(args.planner), f"Planner configuration file {args.planner} does not exist"
    with open(args.planner) as f:
        planner_configuration = json.load(f)
    bspace_dims = construct_behaviour_space(args, planner_configuration, task)
    planner_configuration['planner-parameters']['base-planner-cfg']['k'] = args.k_plans
    planner_configuration['planner-parameters']['bspace-cfg']['dims'] = bspace_dims

    for idx, (compilername, compilationkind) in enumerate(planner_configuration['planner-parameters']['bspace-cfg']['compliation-list']):
        planner_configuration['planner-parameters']['bspace-cfg']['compliation-list'][idx] = [compilername, eval(f"CompilationKind.{compilationkind}")]

    return planner_configuration

def _is_valid_file(arg: str) -> str:
    """
    Checks whether input PDDL files exist and are valid
    Args: arg (str): The path to the PDDL file.
    Returns: str: The validated path to the PDDL file.
    Raises:
        argparse.ArgumentTypeError: If the file does not exist or is not a PDDL file.
    """
    if not os.path.exists(arg):
        raise argparse.ArgumentTypeError('{} not found!'.format(arg))
    elif not (os.path.splitext(arg)[1] == ".pddl" or os.path.splitext(arg)[1] == ".ipddl"):
        raise argparse.ArgumentTypeError('{} is not a/an additional information PDDL file'.format(arg))
    else:
        return arg

def can_create_file(arg: str) -> str:
    """
    Check if a file can be created at the specified path.
    
    This function determines whether a file can be created at the given full
    path by checking the existence and write permissions of the directory
    containing the file.

    Args:
        arg (str): The full path where the file is to be created. 
                   This can be an absolute or relative path.

    Returns:
        str: The validated path to the file.

    Raises:
        argparse.ArgumentTypeError: If the file cannot be created at the specified path.
    """
    # Extract the directory path from the full path
    full_path = os.path.abspath(arg)  # if relative, transform to absolute
    directory = os.path.dirname(full_path)
    
    # create the directory if it does not exist
    os.makedirs(directory, exist_ok=True)
    
    # Check if the file can be created at the specified path
    if os.access(directory, os.F_OK) and os.access(directory, os.W_OK):
        return arg
    else:
        raise argparse.ArgumentTypeError(f"Cannot create file at {arg}")

def create_parser():
    parser = argparse.ArgumentParser(description = "FBI Driver for Storytelling.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser.add_argument('-p', '--problem', required=True, metavar='problem.pddl',
                        help='Path to PDDL problem file', type=_is_valid_file)
    parser.add_argument('-d', '--domain', required=True, metavar='domain.pddl',
                        help='Path to PDDL domain file', type=_is_valid_file)
    parser.add_argument('-o', '--output', required=True, metavar='output.json',
                        help='Path to output JSON file', type=can_create_file)
    
    parser.add_argument('-c', '--compile-intention', action='store_true', help='Recompile the task to remove intentions')
    
    parser.add_argument('--planner', required=True, metavar='planner.json', help='Path to planner configuration file')
    parser.add_argument('-k', '--k-plans', required=True, metavar='k', help='Number of plans to generate', type=int)
    parser.add_argument('-q', '--quality-bound', required=True, metavar='q', help='Quality bound for the plans', type=float)
    return parser

def get_profiling_dumpfile(args):
    profiling_dir = os.path.join(os.path.dirname(args.output), 'profiling')
    os.makedirs(profiling_dir, exist_ok=True)
    domainnamefile = os.path.basename(os.path.dirname(args.domain))
    problemnamefile = os.path.basename(args.problem).replace('.pddl', '')
    return os.path.join(profiling_dir, f'{domainnamefile}-{problemnamefile}.prof')



def list_storydomains(directory_path):
    planning_problems = []
    for root, dirs, files in os.walk(directory_path):
        for dir_name in dirs:
            if not os.path.exists(os.path.join(root, dir_name, 'api.py')): continue
            for domainsroot, _dir, _files in os.walk(os.path.join(root, dir_name)):
                domainapi = os.path.join(domainsroot, 'api.py')
                _modulename = f'{os.path.basename(domainsroot)}_module'
                if not os.path.exists(domainapi): continue
                module_spec = importlib.util.spec_from_file_location(_modulename, domainapi)
                domain_module = importlib.util.module_from_spec(module_spec)
                module_spec.loader.exec_module(domain_module)
                domainsproblems = deepcopy(domain_module.domains)
                _domainname = domainsproblems[0]['name']
                _ipc_year   = domainsproblems[0]['ipc']
                domainsproblems[0]['problems'].sort(key=lambda x:x[1])
                for no, problem in enumerate(domainsproblems[0]['problems']):
                    _instanceno = no+1
                    planning_problem                = defaultdict(dict)
                    planning_problem['domainname']  = _domainname
                    planning_problem['instanceno']  = _instanceno
                    planning_problem['domainfile']  = os.path.join(os.path.dirname(domainsroot), problem[0])
                    planning_problem['problemfile'] = os.path.join(os.path.dirname(domainsroot), problem[1])
                    planning_problems.append(planning_problem)
                    
    return planning_problems

def listexps(expsdir):
    exps = []
    for root, dirs, files in os.walk(expsdir):
        for dir_name in dirs:
            if not os.path.exists(os.path.join(root, dir_name, 'exp-details.json')): continue
            exps.append((os.path.join(root, dir_name), os.path.join(root, dir_name, 'exp-details.json')))
    return exps

def listplanners(dir):
    planners = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if not file.endswith('.json'): continue
            planners.append(os.path.join(root, file))
    return planners


def readexp(expfile):
    import json
    with open(expfile) as f:
        return json.load(f)

def readplanner(plannerfile):
    import json
    with open(plannerfile) as f:
        return json.load(f)

def contruct_run_cmd(q, k, domainprob, planner, sandboxdir, venv, recompile):
    plannername = os.path.basename(planner).replace('.json', '')
    domain_instance_dir = f'{plannername}_{domainprob["domainname"]}_{domainprob["instanceno"]}_k_{k}_q_{q}'
    rundir = os.path.join(sandboxdir, 'runs')
    resultsdir = os.path.join(sandboxdir, 'results')
    taskrundir = os.path.join(rundir, domain_instance_dir)
    scriptdir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
    ret_cmd  = [f'source {os.path.join(venv, "bin", "activate")}']
    ret_cmd += [f'mkdir -p {taskrundir}']
    ret_cmd += [f'cd {taskrundir}']
    ret_cmd += [runargs(scriptdir, domainprob, planner, os.path.join(resultsdir, f'{domain_instance_dir}-{plannername}-{q}-{k}.json'), k, q, recompile)]
    ret_cmd += ['deactivate']
    return ' && '.join(ret_cmd)

def runargs(scriptdir, domprob, planner, output, k, q, recompile):
    import json
    with open(planner) as f:
        planner_details = json.load(f)

    retcmd = []
    retcmd += ["python3", os.path.join(scriptdir, "generate_diverse_endings.py")]
    retcmd += ["--domain", domprob['domainfile']]
    retcmd += ["--problem", domprob[f'problemfile']]
    retcmd += ["--output", output]
    retcmd += ["--planner", planner]
    retcmd += ["-k", str(k)]
    retcmd += ["-q", str(q)]
    if recompile: retcmd += ["-c"]
    return ' '.join(retcmd)

def slurm_cmd(name, cmd, timelimt, memorylimit, slurmdumpdir, parition):
    return f"""#!/bin/bash
#SBATCH --job-name=task-{name}
#SBATCH -e {slurmdumpdir}/slurm-logs-error/task-{name}.error
#SBATCH -o {slurmdumpdir}/slurm-logs-output/task-{name}.output
#SBATCH --cpus-per-task=1
#SBATCH --mem={memorylimit}
#SBATCH --time={timelimt}

{cmd}
"""

def getkeyvalue(data, target_key):
    if isinstance(data, dict):
        if target_key in data:
            return data[target_key]
        for value in data.values():
            result = getkeyvalue(value, target_key)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = getkeyvalue(item, target_key)
            if result is not None:
                return result
    return None
