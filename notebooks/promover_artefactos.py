"""Promoción explícita de artefactos de data/ (candidatos) a backend/ (vigentes).

A19 (SES-077): antes reentrenar_modelo.py copiaba directo a backend/ y el
notebook histórico podía pisar los mismos nombres con «Run All». Ahora el
pipeline deja candidatos en data/ y este script es el único paso que publica.

Sin argumentos muestra el manifiesto (SHA256 y fecha de cada artefacto, vigente
contra candidato) y no cambia nada. Con --confirmar copia los que difieren,
después de verificar que el modelo candidato se guardó con la versión de
scikit-learn declarada en backend/requirements.txt.

Después de promover un modelo o contexto nuevos hay que recalibrar umbrales
(calibrar_umbrales_riesgo.py, que lee de backend/) y pegar valores y huella en
backend/main.py; /health avisa si quedaron desincronizados.

Uso, desde la raíz del repo:
    python notebooks/promover_artefactos.py
    python notebooks/promover_artefactos.py --confirmar
"""
import hashlib
import re
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / 'data'
BACKEND = RAIZ / 'backend'
ARTEFACTOS = ('modelo_final.pkl', 'columnas_modelo.pkl', 'hotspots_contexto.csv', 'indice_inseguridad_comuna.csv')


def huella(ruta):
    """SHA256 del contenido. En los CSV se normalizan los fines de línea: pandas
    en Windows escribe CRLF y Git los convierte (core.autocrlf), y eso no es un
    cambio de datos (A19, SES-077)."""
    if not ruta.is_file():
        return None
    datos = ruta.read_bytes()
    if ruta.suffix == '.csv':
        datos = datos.replace(b'\r\n', b'\n')
    return hashlib.sha256(datos).hexdigest()


def fecha(ruta):
    return datetime.fromtimestamp(ruta.stat().st_mtime).strftime('%Y-%m-%d %H:%M') if ruta.is_file() else '-'


def version_sklearn_del_pickle(ruta):
    versiones = set(re.findall(rb'_sklearn_version.{1,12}?(\d+\.\d+\.\d+)', ruta.read_bytes(), re.S))
    return versiones.pop().decode() if len(versiones) == 1 else None


def manifiesto():
    filas = []
    for nombre in ARTEFACTOS:
        candidato, vigente = DATA / nombre, BACKEND / nombre
        h_c, h_v = huella(candidato), huella(vigente)
        estado = 'sin candidato' if h_c is None else ('igual' if h_c == h_v else 'DIFIERE')
        filas.append((nombre, estado, h_v, h_c, fecha(vigente), fecha(candidato)))
    return filas


def main():
    confirmar = '--confirmar' in sys.argv
    filas = manifiesto()
    print(f"{'artefacto':32} {'estado':14} {'vigente (backend/)':28} {'candidato (data/)':28}")
    for nombre, estado, h_v, h_c, f_v, f_c in filas:
        print(f"{nombre:32} {estado:14} {(h_v or '-')[:12]} {f_v:15} {(h_c or '-')[:12]} {f_c}")

    a_copiar = [f[0] for f in filas if f[1] == 'DIFIERE']
    if not a_copiar:
        print('\nNada que promover.')
        return
    if not confirmar:
        print(f"\n{len(a_copiar)} difieren. Revisar y volver a correr con --confirmar para publicarlos.")
        return

    if 'modelo_final.pkl' in a_copiar:
        declarada = re.search(r'^scikit-learn==(\S+)$', (BACKEND / 'requirements.txt').read_text(encoding='utf-8'), re.M).group(1)
        del_pickle = version_sklearn_del_pickle(DATA / 'modelo_final.pkl')
        if del_pickle != declarada:
            raise SystemExit(f'El candidato se guardó con scikit-learn {del_pickle}, se declara {declarada}: no se promueve.')
    for nombre in a_copiar:
        (BACKEND / nombre).write_bytes((DATA / nombre).read_bytes())
        print(f'promovido: {nombre}')
    print('\nSiguiente: python notebooks/calibrar_umbrales_riesgo.py y pegar umbrales y huella en backend/main.py.')


if __name__ == '__main__':
    main()
