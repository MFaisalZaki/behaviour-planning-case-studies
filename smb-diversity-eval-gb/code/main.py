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
    os.makedirs(renderdir, exist_ok=True)
    
    dims = []
    dims += [SuperMarioScoreDiversity]
    dims += [SuperMarioCoinsDiversity]
    dims += [SuperMarioTimeleftDiversity]

    print("Generating plans using luigi...")
    luigi = SuperMarioFBIAgent([], romfile)
    luigi_plans = luigi.plan(args.k)
    dump_plans_render(luigi_plans, luigi.env, renderdir, "luigi")
    dump_plans_behaviours(luigi_plans, BehaviourSpace([d(luigi.env) for d in dims], luigi.env), renderdir, 'luigi')

    print("Generating plans using mario...")
    mario = SuperMarioFBIAgent([], romfile)
    mario_plans = mario.plan(args.k)
    dump_plans_render(mario_plans, mario.env, renderdir, "mario")
    dump_plans_behaviours(mario_plans, BehaviourSpace([d(mario.env) for d in dims], mario.env), renderdir, 'mario')
