
from planiverse.problems.real_world_problems.urban_planning.environment import UrbanPlanningEnv
from behaviour_planning_simulators.tree_search.shortcuts import BehaviourSpaceTreeSearch
from behaviour_planning_simulators.tree_search.shortcuts import ForbidBehaviourIterativeTreeSearch
from behaviour_planning_simulators.tree_search.shortcuts import BehaviourCountTreeSearch
from behaviour_planning_simulators.tree_search.fbi.planner.utilities import IWiPlanner

from planiverse.problems.real_world_problems.urban_planning.environment import UrbanPlanningEnv

from behaviour_space_dimensions import SustainabilityTreeSearch, DiversityTreeSearch
from utilities import plot_state

#. start code from here.
env = UrbanPlanningEnv(horizon=20)  # Example horizon, adjust as needed
env.fix_index(1)
_init_state, _ = env.reset()
domain_dims = [["SustainabilityTreeSearch", "{'env':env}"], ["DiversityTreeSearch", "{'env':env}"]]

print("Start planning")
dims = [eval(d[0])(eval(d[1], {'env': env, 'envname': 'urban_planning'})) for d in domain_dims]
planner = ForbidBehaviourIterativeTreeSearch(env, IWiPlanner(env), BehaviourSpaceTreeSearch(env, dims))
plans   = planner.plan(10)

print("Planning done, now counting behaviours")
bspace_counter = BehaviourCountTreeSearch(env, dims, plans)

plot_state(-1, _init_state)

# get the final state from each plan by simulating them
for idx, s in enumerate(map(lambda p: env.simulate(p)[-1], plans)):
    print(f"Plan {idx}: Diversity Score: {s.diversity_score}, Sustainability Score: {s.sustainability_score}")
    plot_state(idx, s)
