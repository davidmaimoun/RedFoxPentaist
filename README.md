git clone https://github.com/davidmaimoun/RedFoxPentaist.git

cd RedFoxPentaist

python3 -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows

pip install -r requirements.txt
python3 run rf_launcher.py --gui
