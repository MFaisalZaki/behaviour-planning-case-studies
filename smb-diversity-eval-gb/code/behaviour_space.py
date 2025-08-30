

class DiversityDim:
    def __init__(self, name, env):
        self.name = name
        self.env = env
        self.domain = set()
    
    def abstract(self, state_trace, actions_list):
        assert False, "This should be implemented by the feature"
    
    def extract_behaviour(self, state_trace, actions_list):
        assert False, "This should be implemented by the feature"

class BehaviourSpace:
    def __init__(self, dimensions, env):
        self.dimensions = dimensions
        self.env = env
    
    def __len__(self):
        return len(self.dimensions)

    def infer(self, state_trace, action_trace):
        """
        This returns two things: behaviour and plan's action represented in ltl formula.
        """
        plan_behaviour = [d.extract_behaviour(state_trace, action_trace) for d in self.dimensions]
        plan_behaviour = f"({' & '.join(plan_behaviour)})" if len(plan_behaviour) > 0 else "false"
        return plan_behaviour, self.extract_plan(action_trace)

    def extract_plan(self, action_trace):
        ' & '.join(f'{a}_{t}' for t,a in enumerate(action_trace))

    def check_behaviour(self, state_trace, actionslist, behaviours):
        if len(behaviours) == 0: return False
        ltl_trace = [dim.abstract(state_trace, actionslist) for dim in self.dimensions]
        # For every element in index I want to merge dicts together
        merged_trace = [dict(kv for d in dicts for kv in d.items()) for dicts in zip(*ltl_trace)]
        return any([b.truth(merged_trace) for b in behaviours])
