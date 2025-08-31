git clone https://github.com/davidmaimoun/RedFoxPentaist.git

cd RedFoxPentaist-mater

python -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows

pip install -r requirements.txt
python3 run rf_launcher.py --gui
