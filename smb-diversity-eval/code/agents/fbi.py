from pcg_benchmark.probs.smbtile.engine.core import MarioWorld, MarioActions, MarioForwardModel
from pcg_benchmark.probs.smbtile.engine.agents.astar import AStarTree, TreeNode, GameStatus, getActionString
from flloat.parser.ltlf import LTLfParser

class SuperMarioPlan:
    def __init__(self, actions, behaviour, planltl):
        self.actions = actions
        self.behaviour = behaviour
        self.planltl = planltl

class BehaviourCount:
    def __init__(self, dims):
        self.dimensions = dims
    def count(self, plans):
        return len(set(p.behaviour for p in plans))

class SuperMarioDiversityDim:
    def __init__(self, name):
        self.name = name
        self.domain = set()
    
    def abstract(self, state_trace, actions_list):
        assert False, "This should be implemented by the feature"
    
    def extract_behaviour(self, state_trace, actions_list):
        assert False, "This should be implemented by the feature"

class SuperMarioPlanDim(SuperMarioDiversityDim):
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
        return self.__actions_representation__(actions_list) | {f'{self.name}_goal_state': state_trace[-1].gameStatus == GameStatus.WIN}
    
    def extract_behaviour(self, state_trace, actions_list):
        ret_behaviour = self.__actions_representation__(actions_list)
        self.domain.add(' & '.join(ret_behaviour.keys()))
        return ret_behaviour

class SuperMarioCoinDim(SuperMarioDiversityDim):
    def __init__(self):
        super().__init__("coins")

    def abstract(self, state_trace, actions_list):
        return {f"t{t}_{self.name}_{w.coins}": True for t, w in enumerate(state_trace)} | {f'{self.name}_goal_state': state_trace[-1].gameStatus == GameStatus.WIN}

    def extract_behaviour(self, state_trace, actions_list):
        ltl_trace = self.abstract(state_trace, [])
        key = list(filter(lambda k:  f'{len(state_trace)-1}_{self.name}' in k, ltl_trace.keys()))[0]
        ret_behaviour_ltl = f"FG({key} & {self.name}_goal_state)"
        self.domain.add(ret_behaviour_ltl)
        return ret_behaviour_ltl

class SuperMarioEnemyDim(SuperMarioDiversityDim):
    def __init__(self):
        super().__init__("enemies_count")
    
    def abstract(self, state_trace, actions_list):
        spriteslist = [[sprite.alive for sprite in state._sprites].count(True) for state in state_trace]
        return {f"t{t}_{self.name}_{spritescount}":True for t, spritescount in enumerate(spriteslist)} | {f'{self.name}_goal_state': state_trace[-1].gameStatus == GameStatus.WIN}

    def extract_behaviour(self, state_trace, actions_list):
        ltl_trace = self.abstract(state_trace, [])
        key = list(filter(lambda k:  f'{len(state_trace)-1}_{self.name}' in k, ltl_trace.keys()))[0]
        ret_behaviour_ltl = f"FG({key} & {self.name}_goal_state)"
        self.domain.add(ret_behaviour_ltl)
        return ret_behaviour_ltl

class SuperMarioBehaviourSpace:
    def __init__(self, dimensions, model):
        self.dimensions = dimensions
        self.model = model
    
    def __state_trace__(self, state):
        _parent = state
        state_trace = [state._model._world]
        actions_list = [state.getNextActions()]
        while _parent._parent != None:
            _parent = _parent._parent
            state_trace.append(_parent._model._world)
            actions_list.append(_parent.getNextActions())
        return state_trace[::-1], actions_list[::-1]

    def infer(self, state):
        state_trace, actionslist = self.__state_trace__(state)
        dims_behaviour = [dim.extract_behaviour(state_trace, actionslist) for dim in filter(lambda d: not isinstance(d, SuperMarioPlanDim), self.dimensions)]
        return f"({' & '.join(dims_behaviour)})"

    def represent_plan(self, state):
        state_trace, actionslist = self.__state_trace__(state)
        dims_behaviour = [dim.extract_behaviour(state_trace, actionslist) for dim in filter(lambda d: isinstance(d, SuperMarioPlanDim), self.dimensions)]
        return f"({' & '.join(dims_behaviour[0].keys())})"

    def check_behaviour(self, state, behaviours):
        if len(behaviours) == 0: return False
        state_trace, actionslist = self.__state_trace__(state)
        ltl_trace = [dim.abstract(state_trace, actionslist) for dim in self.dimensions]
        ltl_trace = {k:v for d in ltl_trace for k,v in d.items()}
        
        if any([b.truth([ltl_trace]) for b in behaviours]):
            return True

        return False

class SuperMarioFBIAgent(AStarTree):
    def __init__(self, dims, killEvents=[]):
        super().__init__(reptitions=8)
        self._killEvents = killEvents
        self.solutions   = []
        plan_dim = SuperMarioPlanDim()
        if not plan_dim in dims:
            self.dimensions = dims + [plan_dim]

    def __construct_world_model__(self, level, timer, marioState=0):
        _world = MarioWorld(self._killEvents)
        _world.initializeLevel(level, 1000 * timer)
        _world.mario.isLarge = marioState > 0
        _world.mario.isFire = marioState > 1
        _world.update([0]*MarioActions.numberOfActions())
        MarioForwardModel.maxMoves = 100
        return MarioForwardModel(_world)

    def search(self, k, level, maxIterations=100, timer=20, plans=[], forbid_behaviours=False):
        model = self.__construct_world_model__(level, timer)
        root = TreeNode(None, self._repetitions, model.clone(), None)
        visitedStates = []
        queue = root.generateChildren()
        bspace = SuperMarioBehaviourSpace(self.dimensions, model.clone())
        ltl_parser = LTLfParser()
        behaviours = [ltl_parser(f'({p.behaviour})')  for p in plans]
        while len(queue) > 0 and maxIterations > 0 and len(self.solutions) < k:
            queue = sorted(queue, key=lambda v: v.getHeuristic() - 0.9 * v.getCost(), reverse=True)
            current = queue.pop(0)
            if self.isInVisited(visitedStates, current.getKey()): continue
            if forbid_behaviours and bspace.check_behaviour(current, behaviours): continue
            visitedStates.append(current.getKey())
            if current._model.getGameStatus() == GameStatus.WIN: 
                self.solutions.append(SuperMarioPlan(current.getNextActions(), bspace.infer(current), bspace.represent_plan(current)))
            queue = queue + current.generateChildren()
            maxIterations -= 1
        return self.solutions
