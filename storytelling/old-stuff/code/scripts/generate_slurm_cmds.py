import sys
import os

from utilities import list_storydomains, contruct_run_cmd, listexps, readexp, listplanners, slurm_cmd
 
def main(args):
    for prefix in ['non-intentional']: # 'intentional', 
        generate_for(args, prefix)


def generate_for(args, prefix):
    parition = 'sturm-part'
    venvdir = os.path.join(os.path.dirname(__file__), '..', 'venv')
    expdir = os.path.join(os.path.dirname(__file__), '..', 'experiments')
    domainsdir = os.path.join(os.path.dirname(__file__), '..', f'pddl-domains-{prefix}')
    sandboxdir = os.path.join(os.path.dirname(__file__), '..', f'sandbox-{prefix}')

    # create dirs
    for dir in ['runs', 'slurm-logs-output', 'slurm-logs-error', 'results']: os.makedirs(os.path.join(sandboxdir, dir), exist_ok=True)

    # get the list of experiments
    cmds = []
    for expdir, expfile in listexps(expdir):
        expdetails = readexp(expfile)
        for plannerfile in listplanners(os.path.join(expdir, 'planners')):
            for domain_problem in list_storydomains(domainsdir):
                for q in expdetails['q']:
                    for k in expdetails['k']:
                        taskname = f'{prefix}-{os.path.basename(plannerfile).replace(".json","")}-{domain_problem["domainname"]}_{domain_problem["instanceno"]}_{k}'
                        cmds.append((taskname, expdetails, contruct_run_cmd(q, k, domain_problem, plannerfile, sandboxdir, venvdir, prefix == 'intentional')))
    
    slurm_cmds = []
    for cmdname, taskdetail, taskcmd in cmds:
        timelimit = taskdetail['timelimit']
        memorylimit = taskdetail['memorylimit']
        slurm_cmds.append((cmdname, slurm_cmd(cmdname, taskcmd, timelimit, memorylimit, sandboxdir, parition)))
        pass

    dumpslurmdir = os.path.join(sandboxdir, 'slurm-cmds')
    os.makedirs(dumpslurmdir, exist_ok=True)
    for i, (_cmdname, _cmd) in enumerate(slurm_cmds):
        with open(os.path.join(dumpslurmdir, f"{prefix}-task-{i}-{_cmdname}.slurm"), 'w') as f:
            f.write(_cmd)

    pass

if __name__ == '__main__':
    main(sys.argv[1:])