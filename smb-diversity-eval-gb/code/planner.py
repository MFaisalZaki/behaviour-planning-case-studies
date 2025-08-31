
from flloat.parser.ltlf import LTLfParser

from env_case_study import SuperMarioCaseStudy
from behaviour_space import BehaviourSpace, DiversityDim
from utilities import PriorityQueue, dump_plan


class SuperMarioScoreDiversity(DiversityDim):
	def __init__(self, env):
		super().__init__('score', env)
		self.domain = set()
	
	def abstract(self, state_trace, actions_list):
		return [{f'{self.name}_{s.score}':True, f'{self.name}_goal_state':self.env.is_goal(s)} for s in state_trace[::-1]]
	
	def extract_behaviour(self, state_trace, actions_list):
		state_ltl_trace = self.abstract(state_trace, actions_list)
		return f'FG({ " & ".join(state_ltl_trace[-1].keys()) })'

class SuperMarioCoinsDiversity(DiversityDim):
	def __init__(self, env):
		super().__init__('coins', env)
		self.domain = set()
	
	def abstract(self, state_trace, actions_list):
		return [{f'{self.name}_{s.coins}':True, f'{self.name}_goal_state':self.env.is_goal(s)} for s in state_trace[::-1]]
	
	def extract_behaviour(self, state_trace, actions_list):
		state_ltl_trace = self.abstract(state_trace, actions_list)
		return f'FG({ " & ".join(state_ltl_trace[-1].keys()) })'


class SuperMarioTimeleftDiversity(DiversityDim):
	def __init__(self, env):
		super().__init__('timeleft', env)
		self.domain = set()
	
	def __categorise__(self, value):
		if value < 100: return 'less_100'
		if value < 200: return 'less_200'
		if value < 300: return 'less_300'
		if value <= 400: return 'less_400'
		return 'full'

	def abstract(self, state_trace, actions_list):
		# So mario timer is 400
		# so let's create a categorial range.
		# less_100, less_200, less_300, less_400
		return [{f'{self.name}_{self.__categorise__(s.timeleft)}':True, f'{self.name}_goal_state':self.env.is_goal(s)} for s in state_trace[::-1]]
	
	def extract_behaviour(self, state_trace, actions_list):
		state_ltl_trace = self.abstract(state_trace, actions_list)
		return f'FG({ " & ".join(state_ltl_trace[-1].keys()) })'

class SuperMarioPlan:
	def __init__(self, actions, behaviour, action_ltl):
		self.actions = actions
		self.behaviour = behaviour
		self.action_ltl = action_ltl
	
	def __eq__(self, other):
		return self.actions == other.actions


class SuperMarioFBIAgent:
	def __init__(self, dims, romfile):
		self.romfile = romfile
		self.env = SuperMarioCaseStudy(romfile)
		self.env.fix_index(0)
		_, _ = self.env.reset()
		self.bspace = BehaviourSpace([d(self.env) for d in dims], self.env)
		self.generated_plans = []

		# IW search required variables.
		self.i = None

	def __cost_fn__(self, state_trace, action_trace):
		penalties = 0
		# consider the down action, this should be costly if mario keeps pressing down for several rounds.
		if ['down' in str(a) for a in action_trace].count(True) / len(action_trace) > 0.3: penalties += 5
		if ['nop' in str(a) for a in action_trace].count(True)  / len(action_trace) > 0.3: penalties += 5
		# also push if mario keeps going right then left multiple time.
		return action_trace[-1].cost() + penalties
	
	def __heuristic__fn__(self, state_trace, action_trace):
		# Considering level_progress only
		lt = [state.level_progress for state in state_trace[::-1]]
		# Consdering velocity vector with level_progress # I doubt the x velocity cound have a neg value.
		# lt = [state.level_progress * state.mario_velocity.x for state in state_trace[::-1]]
		dir_vector = [lt[i+1]-lt[i] for i in range(len(lt)-1)]
		positive_count = len([d for d in dir_vector if d > 0])
		negative_count = len(dir_vector) - positive_count
		confidence = abs(positive_count - negative_count) / len(dir_vector) if len(dir_vector) > 0 else 0
		factor = 1
		return -1*sum(dir_vector)*confidence*factor + 10000 * state_trace[0].mario_damage()
		# Old heuristic
		root  = state_trace[-1]   
		state = state_trace[0]
		return (root.level_progress - state.level_progress) + 1000 * state.mario_damage()
	
	def __search__(self, k, forbid_behaviour):
		# return self.__iw_search__(k, forbid_behaviour)
		return self.__astar_search__(k, forbid_behaviour)
	
	def __forbid_solution__(self, action_trace, plansltls):
		if len(plansltls) == 0: return False
		return any([p.truth([{f'{a}_{t}':True  for t,a in enumerate(action_trace)}]) for p in plansltls])

	def __astar_search__(self, k, forbid_behaviour):
		queue = PriorityQueue()
		state, _ = self.env.reset()
		queue.push(([state], []), 0)
		plans = []
		ltl_parser = LTLfParser()
		behaviours = [ltl_parser(f'({p.behaviour})') for p in self.generated_plans]
		plansltl   = [ltl_parser(f'({p.action_ltl})') for p in self.generated_plans]
		while len(plans) < k and not queue.is_empty():
			state_trace, action_trace = queue.pop()
			state = state_trace[0]
			if self.__forbid_solution__(action_trace, plansltl): continue
			if forbid_behaviour and self.bspace.check_behaviour(state_trace, action_trace, behaviours): continue
			if self.env.is_goal(state):
				plans.append(SuperMarioPlan(action_trace, *self.bspace.infer(state_trace, action_trace)))
				behaviours.append(ltl_parser(f'({plans[-1].behaviour})'))
				plansltl.append(ltl_parser(f'({plans[-1].action_ltl})'))
				print(f"Found plan with behaviour: {plans[-1].behaviour}")
				continue
			for action, successor_state in self.env.successors(state):
				successor_state_trace  = [successor_state] + state_trace
				successor_action_trace = action_trace + [action]
				if self.env.is_terminal(successor_state): continue
				key = self.__heuristic__fn__(successor_state_trace, successor_action_trace) + self.__cost_fn__(successor_state_trace, successor_action_trace)
				queue.push((successor_state_trace, successor_action_trace), key)
		return plans
	
	def __iw_search__(self, k, forbid_behaviour):
		if self.i is None:
			# for i in range(1 if self.i is None else self.i, 1000):
			for i in range(1, 1000):
				solutions = self.__bfs__(i, k, forbid_behaviour)
				if len(solutions) > 0: 
					self.i = i if self.i is None else self.i
					return solutions
			return []
		else:
			return self.__bfs__(self.i, k, forbid_behaviour)
	
	def __bfs__(self, i, k, forbid_behaviour):
		print(f"Searching for plans with i = {i}")
		queue      = []
		state, _   = self.env.reset()
		plans      = []
		visited    = set()
		ltl_parser = LTLfParser()
		behaviours = [ltl_parser(f'({p.behaviour})') for p in self.generated_plans]
		queue.append(([state], [], state.literals))
		while (len(queue) > 0):
			state_trace, action_trace, literals_history = queue.pop(0)
			state = state_trace[0]
			if state.literals in visited: continue
			visited.add(state.literals)
			if self.env.is_goal(state):
				plans.append(SuperMarioPlan(action_trace, *self.bspace.infer(state_trace, action_trace)))
				continue
			for action, successor_state in self.env.successors(state):
				successor_state_trace  = [successor_state] + state_trace
				successor_action_trace = action_trace + [action]
				if self.env.is_terminal(successor_state): continue
				if forbid_behaviour and self.bspace.check_behaviour(successor_state_trace, successor_action_trace, behaviours): continue
				if len(frozenset(successor_state.literals) - literals_history) < i: continue
				queue.append((successor_state_trace, successor_action_trace, frozenset.union(frozenset(successor_state.literals), literals_history)))
		return plans

	def plan(self, k):
		return self.__search__(k, len(self.bspace) != 0)
	
		# there is no dimensions provided, assume top-k.
		if len(self.bspace) == 0:  
			self.generated_plans = self.__search__(k, False)
		else:
			for _ in range(k):
				self.generated_plans += self.__search__(1, True)
		
		return self.generated_plans