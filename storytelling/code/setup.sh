python3.11 -m venv venv
source venv/bin/activate
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
pip uninstall pypmt
pip install git+https://github.com/pyPMT/pyPMT.git@d44efb71746b3a91e7fb1926b4405bd14f9df33b
pip install seaborn