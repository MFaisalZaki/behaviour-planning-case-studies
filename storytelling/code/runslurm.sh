./setup.sh
source venv/bin/activate
python scripts/generate_slurm_cmds.py
./split-slurm.sh $(pwd)/sandbox-non-intentional/slurm-cmds $(pwd)/sandbox-non-intentional/slurm-cmds-splitted stroy
deactivate