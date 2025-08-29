from pcg_benchmark.probs.smbtile.engine.core import MarioWorld, MarioActions, MarioForwardModel, MarioAgentEvent, MarioResult
from pcg_benchmark.probs.smbtile.engine.agents.astar import AStarTree, TreeNode, GameStatus
from flloat.parser.ltlf import LTLfParser

from .utilities import DiversityDim, SimulationPlanDim

class SuperMarioSimulationPlan:
    def __init__(self, actions, behaviour, planltl, world):
        self.actions       = actions
        self.behaviour     = behaviour
        self.actionsltl    = planltl
        self._world_trace  = []
        self.mario_results = self.__update__(world)
    
    def __update__(self, world):
        _world = world.clone()._world
        gameEvents  = []
        agentEvents = []
        for action in self.actions:
            _world.update(action)
            gameEvents += _world.lastFrameEvents
            agentEvents.append(MarioAgentEvent(action, _world.mario.x,
                    _world.mario.y, int(_world.mario.isLarge) + int(_world.mario.isFire),
                    _world.mario.onGround, _world.currentTick))
            self._world_trace.append(_world.clone())
        return MarioResult(_world, gameEvents, agentEvents)

class SuperMarioCoinDim(DiversityDim):
    def __init__(self):
        super().__init__("coins")

    def abstract(self, state_trace, actions_list):
        return [{f"{self.name}_{state.coins}":True} | {f'{self.name}_goal_state': state.gameStatus == GameStatus.WIN} for state in state_trace]

    def extract_behaviour(self, state_trace, actions_list):
        ltl_trace = self.abstract(state_trace, [])
        ret_behaviour_ltl = f"FG({' & '.join(filter(lambda k:  f'{self.name}' in k, ltl_trace[-1].keys()))})"
        self.domain.add(ret_behaviour_ltl)
        return ret_behaviour_ltl

class SuperMarioEnemyDim(DiversityDim):
    def __init__(self):
        super().__init__("enemies_count")
    
    def abstract(self, state_trace, actions_list):
        return [{f"{self.name}_{[sprite.alive for sprite in state._sprites].count(True)}":True} | {f'{self.name}_goal_state': state.gameStatus == GameStatus.WIN} for state in state_trace]

    def extract_behaviour(self, state_trace, actions_list):
        ltl_trace = self.abstract(state_trace, [])
        ret_behaviour_ltl = f"FG({' & '.join(filter(lambda k:  f'{self.name}' in k, ltl_trace[-1].keys()))})"
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
        dims_behaviour = [dim.extract_behaviour(state_trace, actionslist) for dim in filter(lambda d: not isinstance(d, SimulationPlanDim), self.dimensions)]
        return f"({' & '.join(dims_behaviour)})" if len(dims_behaviour) > 0 else "false"

    def represent_plan(self, state):
        state_trace, actionslist = self.__state_trace__(state)
        dims_behaviour = [dim.extract_behaviour(state_trace, actionslist) for dim in filter(lambda d: isinstance(d, SimulationPlanDim), self.dimensions)]
        return f"({' & '.join(dims_behaviour[0].keys())})"

    def check_behaviour(self, state, behaviours):
        if len(behaviours) == 0: return False
        state_trace, actionslist = self.__state_trace__(state)
        ltl_trace = [dim.abstract(state_trace, actionslist) for dim in filter(lambda d: not isinstance(d, SimulationPlanDim), self.dimensions)]
        # For every element in index I want to merge dicts together
        merged_trace = [dict(kv for d in dicts for kv in d.items()) for dicts in zip(*ltl_trace)]
        return any([b.truth(merged_trace) for b in behaviours])

class SuperMarioFBIAgent(AStarTree):
    def __init__(self, dims, killEvents=[]):
        super().__init__(reptitions=3)
        self._killEvents = killEvents
        plan_dim = SimulationPlanDim()
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

    def __forbid_plan__(self, bspace, state, plansltl):
        if len(plansltl) == 0: return False
        plandim = [dim for dim in filter(lambda d: isinstance(d, SimulationPlanDim), bspace.dimensions)][0]
        state_trace, actionslist = bspace.__state_trace__(state)
        ltl_trace = plandim.abstract([], actionslist)
        # plans_ltl_formula.truth([ltl_trace[-1]])
        return any([p.truth([ltl_trace]) for p in plansltl])

    def search(self, k, level, maxIterations=500, timer=50, plans=[], forbid_behaviours=False):
        solutions = []
        model = self.__construct_world_model__(level, timer)
        initial_model = model.clone()
        root = TreeNode(None, self._repetitions, model.clone(), None)
        visitedStates = []
        queue = root.generateChildren()
        bspace = SuperMarioBehaviourSpace(self.dimensions, model.clone())
        ltl_parser = LTLfParser()
        behaviours = [ltl_parser(f'({p.behaviour})')  for p in plans]
        # I don't think we need the maxIterations termination condition.
        # while len(queue) > 0 and maxIterations > 0 and len(solutions) < k:
        while len(queue) > 0 and len(solutions) < k:
            queue = sorted(queue, key=lambda v: v.getHeuristic() - 0.9 * v.getCost(), reverse=True)
            current = queue.pop(0)
            if self.isInVisited(visitedStates, current.getKey()): continue
            if forbid_behaviours and bspace.check_behaviour(current, behaviours): continue
            # if self.__forbid_plan__(bspace, current, [ltl_parser(f'({p.actionsltl})') for p in self.solutions + plans]): continue
            visitedStates.append(current.getKey())
            if current._model.getGameStatus() == GameStatus.WIN: 
                solutions.append(SuperMarioSimulationPlan(current.getNextActions(), bspace.infer(current), bspace.represent_plan(current), initial_model))
                bspace.check_behaviour(current, behaviours)
            queue = queue + current.generateChildren()
            maxIterations -= 1
        return solutions
