
from pcg_benchmark.probs.smbtile.engine.agents.astar import getActionString
from pcg_benchmark.probs.smbtile.engine.agents.astar import GameStatus

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
