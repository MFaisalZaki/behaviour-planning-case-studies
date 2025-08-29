from pcg_benchmark.probs.smbtile.engine.core import MarioAgent, MarioGame
from pcg_benchmark.probs.smbtile.engine.core import MarioGame
from pcg_benchmark.probs.smbtile.engine.agents.astar import Agent
import pcg_benchmark

from agents.fbi import BehaviourCount, SuperMarioFBIAgent, SuperMarioCoinDim, SuperMarioEnemyDim

env = pcg_benchmark.make("smbtile-v0")

levelString = open('/Users/mustafafaisal/Developer/behaviour-planning-case-studies/smb-diversity-eval/venv/lib/python3.12/site-packages/pcg_benchmark/probs/smb/slices.txt').read()

dims = [SuperMarioCoinDim(), SuperMarioEnemyDim()]
fbiagent_naive = SuperMarioFBIAgent(dims)
plans = fbiagent_naive.search(5, levelString)

bc_count = BehaviourCount(dims).count(plans)

pass
diverse_plans = []
while len(diverse_plans) < 5:
    fbiagent_diverse = SuperMarioFBIAgent(dims)
    plans = fbiagent_diverse.search(1, levelString, plans=diverse_plans, forbid_behaviours=True)
    if len(plans) == 0: break
    diverse_plans.extend(plans)



MarioAgent.iterations = 100
MarioAgent.stickyActions = 8
game = MarioGame()

sol = game.runGame(Agent(None), levelString, 20, 0)



pass