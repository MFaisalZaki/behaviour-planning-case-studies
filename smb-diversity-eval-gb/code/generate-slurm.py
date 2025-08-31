import os
from utilities import create_parser

def get_slurm_command(cmd, taskname, timelimt, memorylimit, slurmdumpdir):
    return f"""#!/bin/bash
#SBATCH --job-name={taskname}
#SBATCH -e {slurmdumpdir}/{taskname}.error
#SBATCH -o {slurmdumpdir}/{taskname}.output
#SBATCH --cpus-per-task=1
#SBATCH --mem={memorylimit}
#SBATCH --time={timelimt}

{cmd}
"""


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    assert os.path.exists(args.romfile), "ROM file does not exist"
    os.makedirs(args.render_dir, exist_ok=True)
    slurm_dir = os.path.join(args.render_dir, "slurm-scripts")
    slurm_log = os.path.join(args.render_dir, "slurm-logs")
    os.makedirs(slurm_dir, exist_ok=True)
    os.makedirs(slurm_log, exist_ok=True)

    for agent in ["luigi", "mario"]:
        taskname = f"{agent}"
        cmd  = f"source {os.path.join(os.path.dirname(__file__), '..', 'venv', 'bin', 'activate')} && "
        cmd += f"python3 {os.path.abspath(__file__).replace('generate-slurm.py', 'main.py')} --romfile {args.romfile} --render-dir {args.render_dir} -k {args.k} --agent {agent}"
        cmd += " && deactivate"
        slurm_script = get_slurm_command(cmd, taskname, "24:00:00", "100G", slurm_log)
        with open(os.path.join(slurm_dir, f"{taskname}.sh"), "w") as f:
            f.write(slurm_script)
        print(f"SLURM script for {agent} written to {os.path.join(slurm_dir, f'{taskname}.sh')}")

    pass