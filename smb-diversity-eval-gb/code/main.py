import os

from planner import SuperMarioFBIAgent, SuperMarioScoreDiversity, SuperMarioCoinsDiversity, SuperMarioTimeleftDiversity
from utilities import dump_plan

current_file_path = os.path.dirname(os.path.abspath(__file__))
sml_romfile = os.path.join(current_file_path, "sandbox", "SuperMarioLand.gb")
dumpstates_images = os.path.join(current_file_path, "sandbox", "dump")
os.makedirs(dumpstates_images, exist_ok=True)


dims = []
dims += [SuperMarioScoreDiversity]
dims += [SuperMarioCoinsDiversity]
dims += [SuperMarioTimeleftDiversity]
mario = SuperMarioFBIAgent(dims, sml_romfile)
plans = mario.plan(3)

# luigi = SuperMarioFBIAgent([], sml_romfile)
# plans = luigi.plan(3)

# dump_plan(plans[0], luigi.env, os.path.join(current_file_path, "sandbox-luigi"))

pass




# from env_case_study import SuperMarioCaseStudy
# from planner import astar_search

# # from planiverse.problems.retro_games.super_mario_bros_gb import SuperMario, SuperMarioAction
# # from code.planner import astar_search

# env = SuperMarioCaseStudy(sml_romfile)
# env.fix_index(0)
# init_state, _ = env.reset()

# plan = astar_search(init_state, env)
pass

# pass