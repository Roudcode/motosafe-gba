"""
T04: pruebas de consumir_metricas.py sin depender del backend real --
mockean la respuesta HTTP de /metrics para probar la retención y el
formato de los snapshots, que es la lógica que de verdad queremos
verificar (no si la red funciona).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import consumir_metricas as cm


def _metricas_falsas():
    return {"/hotspots": {"conteo": 3, "errores_4xx": 0, "errores_5xx": 0, "latencia_promedio_ms": 12.5}}


def test_correr_escribe_un_snapshot_nuevo(tmp_path):
    ruta_log = tmp_path / "metricas_historico.jsonl"
    ahora = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)

    with patch.object(cm, "pedir_metricas", return_value=_metricas_falsas()):
        resultado = cm.correr("http://fake/metrics", ruta_log, retencion_dias=30, ahora=ahora)

    assert resultado["total_conservados"] == 1
    assert resultado["descartados_por_retencion"] == 0
    guardados = cm.leer_snapshots(ruta_log)
    assert len(guardados) == 1
    assert guardados[0]["metricas"] == _metricas_falsas()
    assert guardados[0]["capturado_en"] == ahora.isoformat()


def test_recorta_snapshots_mas_viejos_que_la_retencion():
    ahora = datetime(2026, 10, 21, tzinfo=timezone.utc)
    viejo = {"capturado_en": (ahora - timedelta(days=31)).isoformat(), "metricas": {}}
    limite = {"capturado_en": (ahora - timedelta(days=29)).isoformat(), "metricas": {}}
    nuevo = {"capturado_en": ahora.isoformat(), "metricas": {}}

    conservados = cm.recortar_por_retencion([viejo, limite, nuevo], retencion_dias=30, ahora=ahora)

    assert viejo not in conservados
    assert limite in conservados
    assert nuevo in conservados
    assert len(conservados) == 2


def test_correr_mantiene_historial_entre_corridas_sucesivas(tmp_path):
    ruta_log = tmp_path / "metricas_historico.jsonl"
    primera = datetime(2026, 10, 1, tzinfo=timezone.utc)
    segunda = datetime(2026, 10, 2, tzinfo=timezone.utc)

    with patch.object(cm, "pedir_metricas", return_value=_metricas_falsas()):
        cm.correr("http://fake/metrics", ruta_log, retencion_dias=30, ahora=primera)
        resultado = cm.correr("http://fake/metrics", ruta_log, retencion_dias=30, ahora=segunda)

    assert resultado["total_conservados"] == 2
    guardados = cm.leer_snapshots(ruta_log)
    assert [s["capturado_en"] for s in guardados] == [primera.isoformat(), segunda.isoformat()]


def test_una_linea_corrupta_no_rompe_la_lectura_del_resto(tmp_path):
    ruta_log = tmp_path / "metricas_historico.jsonl"
    buena = {"capturado_en": datetime(2026, 10, 1, tzinfo=timezone.utc).isoformat(), "metricas": {}}
    ruta_log.write_text(json.dumps(buena) + "\n" + "{linea rota sin cerrar" + "\n", encoding="utf-8")

    snapshots = cm.leer_snapshots(ruta_log)

    assert snapshots == [buena]


def test_pedir_metricas_propaga_el_error_en_vez_de_inventar_un_resultado():
    import urllib.error

    with patch.object(cm.urllib.request, "urlopen", side_effect=urllib.error.URLError("sin conexión")):
        try:
            cm.pedir_metricas("http://fake/metrics")
            assert False, "debería haber lanzado URLError"
        except urllib.error.URLError:
            pass
