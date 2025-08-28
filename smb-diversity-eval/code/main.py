from pcg_benchmark.probs.smbtile.engine.core import MarioAgent, MarioGame
from pcg_benchmark.probs.smbtile.engine.core import MarioGame
from pcg_benchmark.probs.smbtile.engine.agents.astar import Agent
import pcg_benchmark

from agents.fbi import SuperMarioFBIAgent, SuperMarioCoinDim, SuperMarioEnemyDim

env = pcg_benchmark.make("smbtile-v0")

levelString = open('/Users/mustafafaisal/Developer/behaviour-planning-case-studies/smb-diversity-eval/venv/lib/python3.12/site-packages/pcg_benchmark/probs/smb/slices.txt').read()

dims = [SuperMarioCoinDim(), SuperMarioEnemyDim()]
fbiagent = SuperMarioFBIAgent(dims)
plans = fbiagent.search(2, levelString)

MarioAgent.iterations = 100
MarioAgent.stickyActions = 8
game = MarioGame()

sol = game.runGame(Agent(None), levelString, 20, 0)



pass