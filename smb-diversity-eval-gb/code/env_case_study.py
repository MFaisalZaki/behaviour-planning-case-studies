# In here we are creating a crafted scenario for testing the planner.


from itertools import chain
from planiverse.problems.retro_games.super_mario_bros_gb import SuperMarioEnv

class SuperMarioCaseStudy(SuperMarioEnv):
    def __init__(self, romfile, render=False):
        super().__init__(romfile, render)
        # overload the action space.
        action_list  = list()
        # action_list += list(chain.from_iterable([[f'{a},{t}' for a in ['a+left', 'a+right']] for t in [10, 15]]))
        action_list += list(chain.from_iterable([[f'{a},{t}' for a in ['a+left', 'a+right']] for t in [3, 10, 15]]))
        # action_list += list(chain.from_iterable([[f'{a},{t}' for a in ['nop']] for t in [3]]))
        action_list += list(chain.from_iterable([[f'{a},{t}' for a in ['left', 'right']] for t in [3]]))
        self.actions = action_list

    def is_goal(self, state):
        # We will stop when the level progress if greater than or equal 432.
        return state.level_progress >= 430
