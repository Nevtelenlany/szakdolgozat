import sys
from pathlib import Path

# megkeresi a projekt legfelső, közös mappáját (ahol a tests, src, data stb. van)
gyoker_mappa = Path(__file__).resolve().parent.parent

# hozzáadja a projekt gyökerét a keresési útvonalához
sys.path.insert(0, str(gyoker_mappa))

# hozzáadjuk az 'src' mappát is mert a backend mappa azon belül van
sys.path.insert(0, str(gyoker_mappa / "src"))