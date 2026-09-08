from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from make_v6_editorial_figures import render_one
render_one('FigE03', stage='final')
