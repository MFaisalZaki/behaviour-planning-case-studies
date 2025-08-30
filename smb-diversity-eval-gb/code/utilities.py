
class PriorityQueue:
    def __init__(self):
        self._elements = []

    def push(self, item, priority):
        self._elements.append((item, priority))
        self._elements.sort(key=lambda x: x[1])

    def pop(self):
        return self._elements.pop(0)[0]

    def is_empty(self):
        return len(self._elements) == 0


def dump_plan(plan, env, dir):
    import os
    os.makedirs(dir, exist_ok=True)
    for t, (act, state) in enumerate(zip(plan, env.simulate(plan))):
        state.save(env.romfile, os.path.join(dir, f"0_t_{t}_{str(act)}.png"))