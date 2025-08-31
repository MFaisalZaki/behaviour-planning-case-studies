import os

from planner import SuperMarioFBIAgent, SuperMarioScoreDiversity, SuperMarioCoinsDiversity, SuperMarioTimeleftDiversity
from behaviour_space import BehaviourSpace
from utilities import dump_plans_render, create_parser, dump_plans_behaviours


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    romfile = args.romfile
    renderdir = args.render_dir
    assert os.path.exists(args.romfile), "ROM file does not exist"
    assert args.agent in ["luigi", "mario"], "Agent must be either 'luigi' or 'mario'"
    
    dims = []
    dims += [SuperMarioScoreDiversity]
    dims += [SuperMarioCoinsDiversity]
    dims += [SuperMarioTimeleftDiversity]

    agent = SuperMarioFBIAgent([], romfile) if args.agent == "luigi" else SuperMarioFBIAgent(dims, romfile)
    print(f"Generating plans using {args.agent}...")
    plans = agent.plan(args.k)
    print(f"Rendering plans for {args.agent}...")
    os.makedirs(renderdir, exist_ok=True)
    dump_plans_render(plans, agent.env, renderdir, args.agent)
    print(f"Dumping plans behaviours for {args.agent}...")
    dump_plans_behaviours(plans, BehaviourSpace([d(agent.env) for d in dims], agent.env), renderdir, args.agent)