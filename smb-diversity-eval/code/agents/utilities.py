import os

from PIL import Image
from pcg_benchmark.probs.smbtile.engine.agents.astar import getActionString
from pcg_benchmark.probs.smbtile.engine.agents.astar import GameStatus
import pcg_benchmark.probs.smbtile.engine.core as smb_core
import pcg_benchmark.probs.smb.engine.helper as smb_helper

class BehaviourCount:
	def __init__(self, dims):
		self.dimensions = dims
		self.behaviours = set()

	def count(self, plans):
		self.behaviours = set(p.behaviour for p in plans)
		return len(self.behaviours)

	def get_behaviours(self):
		return self.behaviours
	
class DiversityDim:
	def __init__(self, name):
		self.name = name
		self.domain = set()
	
	def abstract(self, state_trace, actions_list):
		assert False, "This should be implemented by the feature"
	
	def extract_behaviour(self, state_trace, actions_list):
		assert False, "This should be implemented by the feature"

class SimulationPlanDim(DiversityDim):
	def __init__(self):
		super().__init__("plan")

	def __actions_representation__(self, plan_actions):
		action_string = {}
		for t, action in enumerate(plan_actions):
			for it, a in enumerate(action):
				actionname = getActionString(a).strip().lower().replace(' ', '_')
				action_string[f't{t}_it{it}_{actionname}'] = True
		return action_string

	def abstract(self, state_trace, actions_list):
		ret_ltl_trace = self.__actions_representation__(actions_list)
		if len(state_trace) > 0:
			ret_ltl_trace |= {f'{self.name}_goal_state': state_trace[-1].gameStatus == GameStatus.WIN}
		return ret_ltl_trace

	def extract_behaviour(self, state_trace, actions_list):
		ret_behaviour = self.__actions_representation__(actions_list)
		self.domain.add(' & '.join(ret_behaviour.keys()))
		return ret_behaviour



def render(level):
	graphics = {
		# empty locations
		0: Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/empty.png").convert('RGBA'),

		# Flag
		"^": Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/flag_top.png").convert('RGBA'),
		"f": Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/flag_white.png").convert('RGBA'),
		"I": Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/flag_middle.png").convert('RGBA'),

		# starting location
		"M": Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/mario.png").convert('RGBA'),

		# Enemies
		"y": Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/spiky.png").convert('RGBA'),
		"g": Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/gomba.png").convert('RGBA'),
		"k": Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/greenkoopa.png").convert('RGBA'),
		"r": Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/redkoopa.png").convert('RGBA'),
		
		# solid tiles
		1:  Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/floor.png").convert('RGBA'),
		39: Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/floor.png").convert('RGBA'),
		2:  Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/solid.png").convert('RGBA'),
		
		# Question Mark Blocks
		8: Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/question_coin.png").convert('RGBA'),
		11: Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/question_coin.png").convert('RGBA'),

		# Brick Blocks
		6: Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/brick.png").convert('RGBA'),
		
		# Coin
		15: Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/coin.png").convert('RGBA'),

		# # # Pipes
		18: Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/tubetop_left.png").convert('RGBA'),
		19: Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/tubetop_right.png").convert('RGBA'),

		20: Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/tube_left.png").convert('RGBA'),
		21: Image.open(os.path.dirname(smb_core.__file__) + '/..'  + "/images/tube_right.png").convert('RGBA'),
	}
	# This will need to be fixed. 
	scale  = 16
	width  = level.level.tileHeight
	height = level.level.tileWidth
	layout = level.level._levelTiles

	lvl_image = Image.new("RGBA", (width*scale, height*scale), (109,143,252,255))
	# print the map.
	for y in range(height):
		for tx in range(width):
			x = width - tx - 1
			shift_x = 0
			if layout[y][x] in graphics:
				lvl_image.paste(graphics[layout[y][x]], (x*scale + shift_x, y*scale, (x+1)*scale + shift_x, (y+1)*scale))
			else:
				print(f"Unknown tile: {layout[y][x]} at {(x,y)}")
	# print sprties
	# for y, row in enumerate(level.level._spriteTemplates):
	# 	for x, sprite in enumerate(row):
	# 		if sprite == smb_helper.SpriteType.NONE: continue
	# 		match sprite:
	# 			case smb_helper.SpriteType.GOOMBA: char = "g"
	# 			case smb_helper.SpriteType.RED_KOOPA: char = "r"
	# 			case smb_helper.SpriteType.GREEN_KOOPA: char = "k"
	# 			case smb_helper.SpriteType.SPIKY: char = "y"
	# 			case _:
	# 				assert False, f"Unknown sprite type {sprite}"
	# 		lvl_image.paste(graphics[char], (x*scale + shift_x, y*scale, (x+1)*scale + shift_x, (y+1)*scale))
	# print Mario
	mario = level._sprites[0]
	print(f"Mario at {(mario.x, mario.y)}")
	lvl_image.paste(graphics["M"], (int(mario.y*scale), int(mario.x*scale), int(mario.y+1 *scale), int(mario.x+1 *scale)))
	return lvl_image

def render_plan(plan):
	return [(t, render(world)) for t, world in enumerate(plan._world_trace)]

def dump_render(imgstrace, dir):
	for t, img in imgstrace:
		img.save(f"{dir}/frame_{t}.png")