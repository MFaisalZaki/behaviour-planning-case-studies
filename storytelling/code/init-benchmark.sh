if [ $# -gt 0 ]; then
    slurmpartname=$1
else
    echo "Usage: $0 <slurmpartname>"
    exit 1
fi

python3.12 -m venv $(pwd)/venv
source $(pwd)/venv/bin/activate
pip install deps/unified-planning-narrative/.
pip install git+https://github.com/MFaisalZaki/pyBehaviourPlanningSMT.git
pip install git+https://github.com/MFaisalZaki/forbiditerative.git
pip install behaviour_space_dims/.

pip uninstall pypmt -y
pip install git+https://github.com/pyPMT/pyPMT.git@d44efb71746b3a91e7fb1926b4405bd14f9df33b
pip install seaborn

python $(pwd)/generate-benchmark-slurm-tasks.py --sandbox-dir $(pwd)/sandbox-benchmark-narrative --planning-tasks-dir $(pwd)/pddl-domains-non-intentional --planning-type narrative

sh $(pwd)/split-slurm.sh $(pwd)/sandbox-non-intentional/slurm-dumps $(pwd)/sandbox-non-intentional/splitted-slurm-dumps storytelling $slurmpartname
deactivate
