import os
import argparse
import json
import importlib.util
from collections import defaultdict, Counter
from copy import deepcopy

from utilities import getkeyvalue

timelimit_map = {
    'fbi-smt' : '01:30:00',
    'fbi-smt-naive' : '01:30:00',
    'fi-bc': '01:45:00',
    'symk': '01:45:00',
}   

def wrap_cmd(taskname, cmd, timelimt, memorylimit, slurmdumpdir):
    return f"""#!/bin/bash
#SBATCH --job-name={taskname}
#SBATCH -e {slurmdumpdir}/{taskname}.error
#SBATCH -o {slurmdumpdir}/{taskname}.output
#SBATCH --cpus-per-task=1
#SBATCH --mem={memorylimit}
#SBATCH --time={timelimt}

{cmd}
"""

def parse_planning_tasks(planningtasksdir:str, resourcesfiledir:str, resourcesdumpdir:str, selected_instances:set):
    # First collect the resoruces information requried.
    resources = _get_resources_details(resourcesfiledir)

    # First collect all the planning tasks from the planning tasks directory.
    planning_domains = _get_planning_domains(planningtasksdir)

    planning_problems = []
    covered_domains = set()
    included_instances = set()
    for domain in planning_domains:
        for domainsroot, _dir, _files in os.walk(domain):
            domainapi = os.path.join(domainsroot, 'api.py')
            _domainbasename = os.path.basename(domainsroot)
            # This is not a valid domain directory.
            if not os.path.exists(domainapi): continue
            # Ignore already processed domains.
            if _domainbasename in covered_domains: continue
            # Process only strips domains.
            if 'adl' in _domainbasename: continue
            _modulename = f'{os.path.basename(domainsroot)}_module'
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
                planning_problem['ipc_year']    = _ipc_year
                planning_problem['domainfile']  = os.path.join(os.path.dirname(domainsroot), problem[0])
                planning_problem['problemfile'] = os.path.join(os.path.dirname(domainsroot), problem[1])

                # If selected instances are not empty, then filter the instances.
                if len(selected_instances) > 0 and f"({str(_ipc_year)}, {_domainname}, {_instanceno})" not in selected_instances: 
                    continue

                # check if the domain and problem instance has resources.
                resourcesfile = None
                if _ipc_year in resources and _domainname in resources[_ipc_year]:
                    if str(_instanceno) in resources[_ipc_year][_domainname]:
                        # maybe I'll consider this later.
                        # dump the resources to a file. 
                        resourcesfile = os.path.join(resourcesdumpdir, f'{_domainname}_{_instanceno}_resources.txt')
                        with open(resourcesfile, 'w') as f:
                            f.write(resources[_ipc_year][_domainname][str(_instanceno)])
                        planning_problem['resources'] = resourcesfile
                
                if not resourcesfile:
                    planning_problem['resources'] = resourcesfile
                
                # Ignore if the domain or problem file does not exist.
                if not (os.path.exists(planning_problem['domainfile']) and os.path.exists(planning_problem['problemfile'])): 
                    continue
                if planning_problem in planning_problems:
                    continue
                if (planning_problem['domainname'], planning_problem['instanceno'], planning_problem['ipc_year']) in included_instances:
                    continue

                included_instances.add((planning_problem['domainname'], planning_problem['instanceno'], planning_problem['ipc_year']))

                planning_problems.append(planning_problem)
                covered_domains.add(os.path.basename(domainsroot))
    
    return planning_problems

def _get_resources_details(resourcesfiledir:str):
    all_resources = defaultdict(dict)
    for root, dirs, files in os.walk(resourcesfiledir):
        for dir_name in dirs:
            domainpath = os.path.join(root, dir_name)
            for resoruce_file in os.listdir(domainpath):
                # load json file and store the data.
                jsonfile = os.path.join(domainpath, resoruce_file)
                with open(jsonfile, 'r') as f:
                    domain_resources = json.load(f)
                year = getkeyvalue(domain_resources, 'year')
                domain = getkeyvalue(domain_resources, 'domain')
                if not year in all_resources: all_resources[year] = defaultdict(dict)
                if not domain in all_resources[year]: all_resources[year][domain] = defaultdict(dict)
                all_resources[year][domain] = domain_resources['instances']
    return all_resources

def _get_planning_domains(directory_path):
    planning_domains = []
    for root, dirs, files in os.walk(directory_path):
        for dir_name in dirs:
            if not os.path.exists(os.path.join(root, dir_name, 'api.py')): continue
            planning_domains.append(os.path.join(root, dir_name))
    return planning_domains

def arg_parser():
    parser = argparse.ArgumentParser(description="Generate SLURM tasks for running experiments.")
    parser.add_argument('--sandbox-dir', type=str, required=True, help='Path to the sandbox directory.')
    parser.add_argument('--planning-tasks-dir', type=str, required=True, help='Directory containing planning tasks.')
    parser.add_argument('--resources-dir', type=str, required=False, default='', help='Directory containing resource files for tasks.')
    parser.add_argument('--planning-type', type=str, required=False, default='classical', help='Type of planning tasks to consider (classical/oversubscription/numerical).')
    return parser

def wrap_tasks_in_slurm_scripts(tasks, slurmdumpdir, timelimit='00:30:00', memorylimit='16G'):
    venv = os.path.join(os.path.dirname(slurmdumpdir), '..', 'venv')
    scriptfile = os.path.join(os.path.dirname(slurmdumpdir), '..', 'paper_experiments', 'run-benchmark.py')
    tasksdir = os.path.join(os.path.dirname(slurmdumpdir), 'tasksdir')
    os.makedirs(tasksdir, exist_ok=True)
    
    resultsdir = os.path.join(os.path.dirname(slurmdumpdir), 'resultsdir')
    os.makedirs(resultsdir, exist_ok=True)

    slurm_scripts = []
    for task in tasks:
        taskfile = os.path.join(tasksdir, f"{task['filename']}")
        with open(taskfile, 'w') as f:
            json.dump(task, f, indent=4)
        rundir = os.path.join(os.path.dirname(slurmdumpdir), 'rundir', task['filename'].replace('.json',''))
        os.makedirs(rundir, exist_ok=True)

        cmd = [f"source {venv}/bin/activate"]
        cmd.append(f"cd {rundir}")
        cmd.append(f"python {scriptfile} --taskfile {taskfile} --outputdir {resultsdir}")
        cmd.append(f"deactivate")
        cmd = " && ".join(cmd)
        slurm_script = wrap_cmd(task['filename'].replace('.json',''), cmd, timelimit_map[task['planner']], memorylimit, slurmdumpdir)
        slurm_scripts.append((task['filename'].replace('.json',''), slurm_script))
    return slurm_scripts

def generate_tasks(planning_tasks_dir, resources_dir, sandboxdir, planning_type):
    _tasks = []
    ru_info_dumps = os.path.join(sandboxdir, 'resource-usage-dumps')
    os.makedirs(ru_info_dumps, exist_ok=True)

    q_list   = []
    planners = []
    selected_instances = set()
    match planning_type:
        case 'narrative':
            q_list   = [1.0, 2.0]
            planners = ['fbi-smt', 'fbi-smt-naive', 'fi-bc', 'symk']
        case _:
            q_list = []

    for task in parse_planning_tasks(planning_tasks_dir, resources_dir, ru_info_dumps, set()):
        for q in q_list:
            for k in [2,5,10,100,1000]:
                for planner in planners:                
                    _tasks.append(task | { 'sandbox-dir' : sandboxdir, 'planning-type': planning_type, 'planner' : planner, 'q': q, 'k-plans': k, 'filename': f"{q}-{k}-{planning_type}-{task['ipc_year']}-{task['domainname']}-{task['instanceno']}-{planner}.json"})
    return _tasks

def main():
    parser = arg_parser()
    args = parser.parse_args()

    sandbox_dir = args.sandbox_dir
    planning_tasks_dir = args.planning_tasks_dir
    resources_dir = args.resources_dir
    planning_type = args.planning_type
    slurmdumpdir  = os.path.join(sandbox_dir, 'slurm-dumps')
    os.makedirs(slurmdumpdir, exist_ok=True)

    print(f"Generating SLURM scripts for planning tasks in {planning_tasks_dir} with resources from {resources_dir} and planning type {planning_type}...")

    slurm_scripts = wrap_tasks_in_slurm_scripts(generate_tasks(planning_tasks_dir, resources_dir, sandbox_dir, planning_type), slurmdumpdir)

    for idx, (taskname, script) in enumerate(slurm_scripts):
        with open(os.path.join(slurmdumpdir, f"{idx}_{taskname}.sh"), 'w') as f:
            f.write(script)

if __name__ == "__main__":
    main()
