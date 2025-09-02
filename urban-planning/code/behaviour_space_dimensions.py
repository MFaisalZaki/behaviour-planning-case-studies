

from behaviour_planning_simulators.tree_search.bss.behaviour_features_library.base import DimensionConstructorTreeSearch


class SustainabilityTreeSearch(DimensionConstructorTreeSearch):
    def __init__(self, additional_infomation:int):
        super().__init__("SustainabilityTreeSearch", additional_infomation)
        self.score_is = 'sustainability_is'
    
    def extract_ltl(self, t, action_trace, states_trace):
        sustainability_score_category = ''

        if states_trace.sustainability_score < 0.2: sustainability_score_category = 'very_low'
        elif states_trace.sustainability_score < 0.3: sustainability_score_category = 'low'
        elif states_trace.sustainability_score < 0.4: sustainability_score_category = 'moderately_low'
        elif states_trace.sustainability_score < 0.5: sustainability_score_category = 'below_average'
        elif states_trace.sustainability_score < 0.6: sustainability_score_category = 'average'
        elif states_trace.sustainability_score < 0.7: sustainability_score_category = 'moderately_high'
        elif states_trace.sustainability_score < 0.8: sustainability_score_category = 'high'
        elif states_trace.sustainability_score < 0.9: sustainability_score_category = 'very_high'
        else: sustainability_score_category = 'ideal'

        # if states_trace.sustainability_score < 0.25 : sustainability_score_category = 'very_low'
        # elif states_trace.sustainability_score < 0.5 : sustainability_score_category = 'average'
        # elif states_trace.sustainability_score < 0.75 : sustainability_score_category = 'high'
        # elif states_trace.sustainability_score < 1.0 : sustainability_score_category = 'very_high'
        # else: sustainability_score_category = 'ideal'

        score_state_ltl = {}
        score_state_ltl[f"{self.plan_found_str}"] = self.env.is_goal(states_trace)
        score_state_ltl[f"{self.score_is}_{sustainability_score_category}"] = True
        score_state_ltl['cost_greater_than_zero'] = len(action_trace) > 0
        return score_state_ltl

    def extract_behaviour_ltl(self, action_trace, ltl_trace):
        # We need to make sure that the planner does not exceed the upper cost bound.
        key = list(filter(lambda k: self.score_is in k, ltl_trace[-1].keys())).pop()
        ret_behaviour_ltl  = []
        ret_behaviour_ltl += [f"FG({key} & {self.plan_found_str})"]
        ret_behaviour_ltl = ' & '.join(ret_behaviour_ltl)
        self.var_domain_values.add(ret_behaviour_ltl)
        self.logs.append([f'behaviour #{len(self.logs)}: {ret_behaviour_ltl}'])
        return ret_behaviour_ltl
        
class DiversityTreeSearch(DimensionConstructorTreeSearch):
    def __init__(self, additional_infomation:int):
        super().__init__("DiversityTreeSearch", additional_infomation)
        self.score_is = 'diversity_is'
    
    def extract_ltl(self, t, action_trace, states_trace):

        diversity_score_category = ''
        if states_trace.diversity_score < 0.2: diversity_score_category = 'very_low'
        elif states_trace.diversity_score < 0.3: diversity_score_category = 'low'
        elif states_trace.diversity_score < 0.4: diversity_score_category = 'moderately_low'
        elif states_trace.diversity_score < 0.5: diversity_score_category = 'below_average'
        elif states_trace.diversity_score < 0.6: diversity_score_category = 'average'
        elif states_trace.diversity_score < 0.7: diversity_score_category = 'moderately_high'
        elif states_trace.diversity_score < 0.8: diversity_score_category = 'high'
        elif states_trace.diversity_score < 0.9: diversity_score_category = 'very_high'
        else: diversity_score_category = 'ideal'

        # if states_trace.diversity_score < 0.25 : diversity_score_category = 'very_low'
        # elif states_trace.diversity_score < 0.35 : diversity_score_category = 'low'
        # elif states_trace.diversity_score < 0.5 : diversity_score_category = 'average'
        # elif states_trace.diversity_score < 0.75 : diversity_score_category = 'high'
        # elif states_trace.diversity_score < 1.0 : diversity_score_category = 'very_high'
        # else: diversity_score_category = 'ideal'

        score_state_ltl = {}
        score_state_ltl[f"{self.plan_found_str}"] = self.env.is_goal(states_trace)
        score_state_ltl[f"{self.score_is}_{diversity_score_category}"] = True
        score_state_ltl['cost_greater_than_zero'] = len(action_trace) > 0
        return score_state_ltl

    def extract_behaviour_ltl(self, action_trace, ltl_trace):
        # We need to make sure that the planner does not exceed the upper cost bound.
        key = list(filter(lambda k: self.score_is in k, ltl_trace[-1].keys())).pop()
        ret_behaviour_ltl  = []
        ret_behaviour_ltl += [f"FG({key} & {self.plan_found_str})"]
        ret_behaviour_ltl = ' & '.join(ret_behaviour_ltl)
        self.var_domain_values.add(ret_behaviour_ltl)
        self.logs.append([f'behaviour #{len(self.logs)}: {ret_behaviour_ltl}'])
        return ret_behaviour_ltl