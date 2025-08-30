
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

    def __cost_fn__(self, state_trace, action_trace):
        penalties = 0
        # consider the down action, this should be costly if mario keeps pressing down for several rounds.
        if ['down' in str(a) for a in action_trace].count(True) > 3: penalties += 5
        # also push if mario keeps going right then left multiple time.

        return action_trace[-1].cost() + penalties
    
    def __heuristic__fn__(self, state_trace, action_trace):
        root  = state_trace[-1]   
        state = state_trace[0]
        return (root.level_progress - state.level_progress) + 1000 * state.mario_damage()

    def __search__(self, k, forbid_behaviour):
        queue = PriorityQueue()
        state, _ = self.env.reset()
        queue.push(([state], []), 0)
        plans = []
        ltl_parser = LTLfParser()
        behaviours = [ltl_parser(f'({p.behaviour})') for p in self.generated_plans]
        while len(plans) < k and not queue.is_empty():
            state_trace, action_trace = queue.pop()
            state = state_trace[0]
            if self.env.is_goal(state):
                plans.append(SuperMarioPlan(action_trace, *self.bspace.infer(state_trace, action_trace)))
                continue
            for action, successor_state in self.env.successors(state):
                successor_state_trace  = [successor_state] + state_trace
                successor_action_trace = action_trace + [action]
                if self.env.is_terminal(successor_state): continue
                if forbid_behaviour and self.bspace.check_behaviour(successor_state_trace, successor_action_trace, behaviours): 
                    continue
                key = self.__heuristic__fn__(successor_state_trace, successor_action_trace) + self.__cost_fn__(successor_state_trace, successor_action_trace)
                queue.push((successor_state_trace, successor_action_trace), key)
        return plans
    
    def plan(self, k):
        # there is no dimensions provided, assume top-k.
        if len(self.bspace) == 0:  
            self.generated_plans = self.__search__(k, False)
        else:
            for _ in range(k):
                self.generated_plans += self.__search__(1, True)
        
        return self.generated_plans