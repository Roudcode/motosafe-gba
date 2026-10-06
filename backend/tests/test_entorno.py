"""A22: el modelo serializado y el entorno declarado tienen que coincidir.

scikit-learn no garantiza cargar un pickle en otra versión. El 07/09 y otra
vez en SES-065 el modelo se guardó con una versión distinta de la declarada
sin que nada lo detectara. Estos tests leen la versión del propio archivo, así
que fallan aunque el venv que los corre tenga cualquier versión instalada.
"""
import re
from pathlib import Path

import main

BACKEND = Path(__file__).resolve().parent.parent


def _version_en_pickle(nombre):
    # El estimador guarda '_sklearn_version' en su estado; sklearn lo descarta
    # al cargarlo, por eso se lee de los bytes y no del objeto.
    contenido = (BACKEND / nombre).read_bytes()
    versiones = set(re.findall(rb'_sklearn_version.{1,12}?(\d+\.\d+\.\d+)', contenido, re.S))
    assert len(versiones) == 1, f'{nombre}: versiones encontradas {versiones}'
    return versiones.pop().decode()


def _version_declarada(paquete):
    texto = (BACKEND / 'requirements.txt').read_text(encoding='utf-8')
    coincidencia = re.search(rf'^{re.escape(paquete)}==(\S+)$', texto, re.M)
    assert coincidencia, f'{paquete} no tiene versión exacta (==) en backend/requirements.txt'
    return coincidencia.group(1)


def test_modelo_entrenado_con_la_version_de_sklearn_declarada():
    assert _version_en_pickle('modelo_final.pkl') == _version_declarada('scikit-learn')


def test_main_detecta_la_version_de_entrenamiento_del_modelo():
    # Si el venv tiene otra versión, main la obtiene del InconsistentVersionWarning;
    # si coincide, no hay aviso y usa la instalada. En ambos casos debe ser la real.
    assert main.SKLEARN_VERSION_ENTRENAMIENTO == _version_en_pickle('modelo_final.pkl')


def test_requirements_backend_fija_versiones_exactas():
    lineas = [
        l.strip() for l in (BACKEND / 'requirements.txt').read_text(encoding='utf-8').splitlines()
        if l.strip() and not l.lstrip().startswith('#')
    ]
    sueltas = [l for l in lineas if '==' not in l]
    assert not sueltas, f'Dependencias sin versión exacta: {sueltas}'


def test_lock_coincide_con_las_versiones_directas_y_tiene_hashes():
    # requirements.lock se genera desde requirements.txt (uv pip compile
    # --universal --generate-hashes, ver docs/operacion/ENTORNO_REPRODUCIBLE.md).
    # Si alguien cambia una versión directa sin regenerar el lock, el
    # Dockerfile y el CI instalarían otra cosa que la declarada.
    def normalizar(nombre):
        return re.sub(r'[-_.]+', '-', nombre).lower()

    lock = (BACKEND / 'requirements.lock').read_text(encoding='utf-8')
    fijadas = {normalizar(n): v for n, v in re.findall(r'^([A-Za-z0-9_.\-]+)==(\S+)', lock, re.M)}
    directas = re.findall(
        r'^([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?==(\S+)$',
        (BACKEND / 'requirements.txt').read_text(encoding='utf-8'), re.M,
    )
    distintas = {n: (v, fijadas.get(normalizar(n))) for n, v in directas if fijadas.get(normalizar(n)) != v}
    assert not distintas, f'Lock desactualizado (declarada, lock): {distintas}'
    sin_hash = [
        bloque.split('==')[0] for bloque in re.split(r'\n(?=[A-Za-z])', lock)
        if '==' in bloque and '--hash=sha256:' not in bloque
    ]
    assert not sin_hash, f'Paquetes sin hash en el lock: {sin_hash}'
