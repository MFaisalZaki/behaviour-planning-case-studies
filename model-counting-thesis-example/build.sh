python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip

pip install git+https://github.com/MFaisalZaki/pyBehaviourPlanningASP.git
pip install git+https://github.com/MFaisalZaki/pyBehaviourPlanningSMT.git
pip uninstall pypmt
pip install git+https://github.com/pyPMT/pyPMT.git@d44efb71746b3a91e7fb1926b4405bd14f9df33b
pip install git+https://github.com/MFaisalZaki/forbiditerative.git
deactivate