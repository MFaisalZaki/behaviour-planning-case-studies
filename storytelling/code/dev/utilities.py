import os

from copy import deepcopy
import unified_planning as up
from unified_planning.io import PDDLReader
from unified_planning.shortcuts import OneshotPlanner, OperatorKind
from up_behaviour_planning.FBIPlannerUp import FBIPlanner

env = up.environment.get_environment()
env.factory.add_engine('FBIPlanner', __name__, 'FBIPlanner')

def update_task_utilities(task):
    goals = {}
    for i, goal in enumerate(task.goals):
        i = i + 1
        if goal.node_type in [OperatorKind.AND, OperatorKind.OR]:
            for j, g in enumerate(goal.args):
                j = j + 1
                goals[g] = i * j
        else:
            goals[goal] = 2**i
    task.add_quality_metric(up.model.metrics.Oversubscription(goals))
    return goals

def get_story_domain(name:str) -> list:
    basedir = os.path.join(os.path.dirname(__file__), 'story-domains-pddl', name)
    assert os.path.exists(basedir), f"Directory {basedir} does not exist"
    domain_file = os.path.join(basedir, f'{name}.pddl')
    assert os.path.exists(domain_file), f"File {domain_file} does not exist"
    # list of files in the directory
    files = sorted(os.listdir(os.path.join(basedir, f'{name}-problems')))
    return [(i, domain_file, os.path.join(basedir, f'{name}-problems', problem)) for i, problem in enumerate(files)]

def generate_stories(domain, problem, planner_params, add_utility):
    task = PDDLReader().parse_problem(domain, problem)
    if add_utility: update_task_utilities(task)
    with OneshotPlanner(name='FBIPlanner',  params=deepcopy(planner_params)) as planner:
        result = planner.solve(task)
    planlist = [] if len(result[0]) < 1 else [r.plan for r in result[0]]
    planlist = list(filter(lambda p: not p is None, planlist))
    logmsgs  = result[1]
    return planlist, logmsgs