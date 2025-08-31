import os
import json
import argparse

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

def create_parser():
    parser = argparse.ArgumentParser(description="Super Mario Bros. Environment")
    parser.add_argument("--romfile", type=str, help="Path to the ROM file")
    parser.add_argument("--render-dir", type=str, help="Render the environment")
    parser.add_argument("-k", type=int, default=3, help="Number of plans to generate")
    parser.add_argument("--agent", type=str, default="luigi", help="Agent to use for planning [luigi for top-k and mario for diverse]")
    return parser

def dump_plan(plan, env, dir):
    import os
    os.makedirs(dir, exist_ok=True)
    for t, (act, state) in enumerate(zip(plan, env.simulate(plan))):
        state.save(env.romfile, os.path.join(dir, f"0_t_{t}_{str(act)}.png"))

def dump_plans_render(plans, env, dir, prefix):
    for idx, plan in enumerate(plans):
        dump_plan(plan.actions, env, os.path.join(dir, f"{prefix}_plan_{idx}"))

def dump_plans_behaviours(plans, bspace, dir, prefix):
    plans_results = {}
    behaviours = set()
    plansltl   = set()
    for idx, plan in enumerate(plans):
        behaviour, planltl = bspace.infer(bspace.env.simulate(plan.actions)[::-1], plan.actions)
        plans_results[f"plan_{idx}"] = {
            "behaviour": behaviour,
            "ltl": planltl,
            "actions": list(map(str, plan.actions)),
            "len": len(plan.actions),
            "cost": sum(a.cost() for a in plan.actions)
        }
        behaviours.add(behaviour)
        plansltl.add(planltl)
    
    plans_results['statistics'] = {
        'behaviour-count' : len(behaviours),
        'plans-count' : len(plansltl), 
        'repeated-plans': len(plans) != len(plansltl)
    }

    os.makedirs(dir, exist_ok=True)
    with open(os.path.join(dir, f"{prefix}_plans_behaviours.json"), 'w') as f:
        json.dump(plans_results, f, indent=4)
    pass