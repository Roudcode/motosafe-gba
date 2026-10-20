import csv
import re
import unicodedata
from difflib import SequenceMatcher
from itertools import combinations

def normalizar(t):
    t = t.lower()
    t = unicodedata.normalize('NFKD', t)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def tokens(t):
    stop = {'el','la','los','las','un','una','de','en','a','y','que','por','con','su','se','al','del','le','lo'}
    return set(w for w in normalizar(t).split() if w not in stop and len(w) > 2)

with open('docs/evidencias/2026-10-06/A09-regeocodificacion/propuesta.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

pares = []
for a, b in combinations(rows, 2):
    if a['fuente'] == b['fuente']:
        continue
    ta, tb = tokens(a['titular']), tokens(b['titular'])
    if not ta or not tb:
        continue
    jacc = len(ta & tb) / len(ta | tb)
    if jacc < 0.25:
        continue
    ratio = SequenceMatcher(None, normalizar(a['titular']), normalizar(b['titular'])).ratio()
    pares.append((jacc, ratio, a, b))

pares.sort(key=lambda x: -x[0])
print(f"{len(pares)} pares cross-fuente con Jaccard >= 0.25 (de {len(rows)} filas, {len(rows)*(len(rows)-1)//2} pares totales)\n")
for jacc, ratio, a, b in pares[:25]:
    print(f"jacc={jacc:.2f} ratio={ratio:.2f}")
    print(f"  [{a['fuente']}] {a['titular']}")
    print(f"  [{b['fuente']}] {b['titular']}")
    print()
