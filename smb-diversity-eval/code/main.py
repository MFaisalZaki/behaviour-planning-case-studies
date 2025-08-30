import numpy as np
from pcg_benchmark.probs.smbtile.engine.core import MarioAgent, MarioGame
from pcg_benchmark.probs.smbtile.engine.core import MarioGame
from pcg_benchmark.probs.smbtile.engine.agents.astar import Agent
from pcg_benchmark.probs.smbtile import MarioProblem
from pcg_benchmark.probs.smbtile.problem import _convert2str
import pcg_benchmark



from agents.fbi import SuperMarioFBIAgent, SuperMarioCoinDim, SuperMarioEnemyDim, SuperMarioScore
from agents.utilities import BehaviourCount, render, render_plan, dump_render

env = pcg_benchmark.make("smbtile-v0")

levelfile = '/Users/mustafafaisal/Developer/behaviour-planning-case-studies/smb-diversity-eval/code/levels/lvl-0.txt'

# levelfile = '/Users/mustafafaisal/Developer/Planiverse/venv-2/lib/python3.12/site-packages/planiverse/problems/retro_games/smb-levels/lvl-1.txt'
convertmap = lambda level: '\n'.join([''.join(row) for row in zip(*level.split('\n'))])
levelString = convertmap(open(levelfile).read())

# levelString = open('/Users/mustafafaisal/Developer/behaviour-planning-case-studies/smb-diversity-eval/venv/lib/python3.12/site-packages/pcg_benchmark/probs/smb/slices.txt').read()

fbiagent_naive = SuperMarioFBIAgent([])

# model = fbiagent_naive.__construct_world_model__(levelString, 50)
# img = render(model._world)
# img.save('/Users/mustafafaisal/Developer/behaviour-planning-case-studies/smb-diversity-eval/sandbox/test.png')
# Now we need to render this....
# naive_plans = fbiagent_naive.search(1, levelString)

# dump_render(render_plan(naive_plans[0]),'/Users/mustafafaisal/Developer/behaviour-planning-case-studies/smb-diversity-eval/sandbox')

pass

# TODO: Simulate a plan
# state_to_print = naive_plans[0]._world_trace[0].level._levelTiles


# pcg_benchmark.register('smbtile-v0-mod', MarioProblem, {'width': len(state_to_print[0]), 'height': len(state_to_print)})

# env = pcg_benchmark.make("smbtile-v0-mod")
# level_content = [list(map(np.int64, row)) for row in plans[0]._world_trace[0].level._levelTiles]
# img = env.render(level_content)


# create a random starting population of 50 individuals (content, info)
# content = env.content_space.sample()

# img = env.render(content)
# img.save('/Users/mustafafaisal/Developer/behaviour-planning-case-studies/smb-diversity-eval/sandbox/test.png')

dims = []
dims += [SuperMarioCoinDim()]
dims += [SuperMarioEnemyDim()]
# dims += [SuperMarioScore()]

k_plans_count = 5

fbiagent_diverse = SuperMarioFBIAgent(dims)
diverse_plans = fbiagent_diverse.search(1, levelString, forbid_behaviours=True)
while len(diverse_plans) < k_plans_count:
    plans = fbiagent_diverse.search(1, levelString, plans=diverse_plans, forbid_behaviours=True)
    if len(plans) == 0: break
    diverse_plans.extend(plans)
    print(f"Found {len(diverse_plans)} diverse plans so far")

bc = BehaviourCount(dims)
bc_count = bc.count(diverse_plans)

MarioAgent.iterations = 100
MarioAgent.stickyActions = 8
game = MarioGame()

sol = game.runGame(Agent(None), levelString, 20, 0)



pass