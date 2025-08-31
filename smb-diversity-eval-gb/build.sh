# Check if the romfile is passed or not.
if [ -z "$1" ]; then
  echo "Usage: $0 <romfile>"
  exit 1
fi

python3.12 -m venv venv
source venv/bin/activate
pip install flloat
pip install git+https://github.com/MFaisalZaki/Planiverse.git
python $(pwd)/code/generate-slurm.py --romfile $1 --render-dir $(pwd)/sandbox-renders -k 3
deactivate