"""A22 (SES-105): run_dev.py tiene que detectar si corre con un interprete
distinto al de venv312, en vez de arrancar en silencio contra el Python de
sistema (sin las versiones fijadas por requirements.lock).
"""
import sys
from pathlib import Path

import pytest

import run_dev


def test_detecta_interprete_correcto(monkeypatch, tmp_path):
    venv = tmp_path / "venv312" / "Scripts"
    venv.mkdir(parents=True)
    python_esperado = venv / "python.exe"
    python_esperado.write_text("")  # alcanza con que exista

    monkeypatch.setattr(run_dev, "__file__", str(tmp_path / "run_dev.py"))
    monkeypatch.setattr(sys, "executable", str(python_esperado))

    run_dev._verificar_interprete_venv()  # no debe lanzar ni salir


def test_corta_si_el_interprete_no_es_el_de_venv312(monkeypatch, tmp_path):
    venv = tmp_path / "venv312" / "Scripts"
    venv.mkdir(parents=True)
    (venv / "python.exe").write_text("")

    otro_python = tmp_path / "python_del_sistema.exe"
    otro_python.write_text("")

    monkeypatch.setattr(run_dev, "__file__", str(tmp_path / "run_dev.py"))
    monkeypatch.setattr(sys, "executable", str(otro_python))

    with pytest.raises(SystemExit) as exc:
        run_dev._verificar_interprete_venv()
    assert "venv312" in str(exc.value)


def test_no_corta_si_no_existe_venv312_todavia(monkeypatch, tmp_path, capsys):
    # Entorno sin venv312 armado (por ejemplo, Docker/CI, que no usa este
    # script): no debe bloquear, solo avisar.
    monkeypatch.setattr(run_dev, "__file__", str(tmp_path / "run_dev.py"))
    monkeypatch.setattr(sys, "executable", str(tmp_path / "cualquier_python"))

    run_dev._verificar_interprete_venv()  # no debe lanzar SystemExit
    assert "AVISO" in capsys.readouterr().err


def test_python_venv312_esperado_usa_bin_python_si_no_hay_scripts(tmp_path):
    (tmp_path / "venv312" / "bin").mkdir(parents=True)
    (tmp_path / "venv312" / "bin" / "python").write_text("")

    import run_dev as m
    original = m.__file__
    try:
        m.__file__ = str(tmp_path / "run_dev.py")
        esperado = m._python_venv312_esperado()
        assert esperado == tmp_path / "venv312" / "bin" / "python"
    finally:
        m.__file__ = original
