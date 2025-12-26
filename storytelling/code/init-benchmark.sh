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
pip install git+https://github.com/MFaisalZaki/up-behaviour-planning.git
pip install git+https://github.com/MFaisalZaki/forbiditerative.git
pip install kstar-planner
pip install behaviour_space_dims/.
git clone https://github.com/IBM/diversescore.git ibm-diversescore
patch -p1 < $(pwd)/scripts/ibm-score-patches/diverscore.1.patch
cd ibm-diversescore
python build.py
cd ..
pip uninstall pypmt -y
pip install git+https://github.com/pyPMT/pyPMT.git@d44efb71746b3a91e7fb1926b4405bd14f9df33b
pip install seaborn

python $(pwd)/generate-benchmark-slurm-tasks.py

sh $(pwd)/split-slurm.sh $(pwd)/sandbox-non-intentional/slurm-dumps $(pwd)/sandbox-non-intentional/splitted-slurm-dumps storytelling $slurmpartname
deactivate
