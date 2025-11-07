import os
import json

from unified_planning.io import PDDLReader, PDDLWriter

from behaviour_planning.over_domain_models.smt.bss.behaviour_features_library.goal_predicate_ordering import GoalPredicatesOrderingSMT
from behaviour_planning.over_domain_models.smt.bss.behaviour_features_library.resource_count import ResourceCountSMT

from behaviour_planning_asp.behaviour_planning import BehaviourPlanning
from behaviour_planning_asp.dims.goal_predicate_ordering import GoalPredicateOrderingDimensionASP
from behaviour_planning_asp.dims.resource_utilisation import ResourceUtilisationDimensionASP

from utilities import fbi_smt_generated_plans, fi_generated_plans, compile_to_asp, stringify_plans

def main():

    k_plan_limit = 5
    q_quality_bound = 1.0

    # First step load the planning problem. 
    current_path = os.path.dirname(os.path.abspath(__file__))
    sandbox_dir = os.path.join(current_path, "sandbox")
    os.makedirs(sandbox_dir, exist_ok=True)

    rovers_dir = os.path.join(current_path, "pddls", "rovers")
    domainfile = os.path.join(rovers_dir, "domain.pddl")
    problemfile = os.path.join(rovers_dir, "p03.pddl")
    task = PDDLReader().parse_problem(domainfile, problemfile)

    # Second step, we need to solve this problem using both FI and FBI with k=1000 and q=1.0
    dims = [
        [GoalPredicatesOrderingSMT, {}],
        [ResourceCountSMT, os.path.join(rovers_dir, "resources.txt")]
    ]

    asp_task = compile_to_asp(task)
    asp_dims = [
        [GoalPredicateOrderingDimensionASP, {}],
        [ResourceUtilisationDimensionASP, {'resourcesfile': os.path.join(rovers_dir, "resources.txt")}]
    ]

    fbi_asp = BehaviourPlanning(encodingname='seq', problem=asp_task.problem, dims_addinfo=asp_dims)

    for planfn in [fbi_smt_generated_plans, fi_generated_plans]:
        plans = planfn(task, domainfile, problemfile, dims, sandbox_dir, k=k_plan_limit, q=q_quality_bound)
        print(f"Generated {len(plans)} plans using {planfn.__name__}")
        statistics = fbi_asp.compute_statistics(stringify_plans(task, plans))
        with open(os.path.join(sandbox_dir, f'statistics_{planfn.__name__}.json'), 'w') as f:
            json.dump(statistics, f, indent=4)

if __name__ == "__main__":
    main()