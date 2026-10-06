"""Pruebas unitarias (pytest) del decodificador de 7 segmentos.

    pip install myhdl pytest
    pytest -v

La logica esta en sevensegdec.py. Los valores esperados (GOLDEN) estan escritos
a mano y NO se leen de tabla.txt: asi la prueba es independiente de la tabla
que verifica (el testbench original comparaba la tabla contra si misma).
"""
from pathlib import Path

import pytest

from sevensegdec import read_table, simulate, convert

TABLA = Path(__file__).with_name("tabla.txt")

# Segmentos encendidos por cada entrada (convencion a-g del taller).
GOLDEN = {
    0: "abcdef",   1: "bc",       2: "abdeg",    3: "abcdg",
    4: "bcfg",     5: "acdfg",    6: "acdefg",   7: "abc",
    8: "abcdefg",  9: "abcdfg",
    10: "g",       # '-'  guion
    11: "d",       # '_'  guion bajo
    12: "a",       # '‾'  sobrerraya
    13: "abfg",    # '°'  grado
    14: "adg",     # '≡'  tres barras
    15: "abcd",    # ']'  corchete derecho
}


def seg_a_int(segs: str) -> int:
    """'bc' -> 0b0110000 (a es el MSB, g el LSB)."""
    return sum(1 << (6 - "abcdefg".index(s)) for s in segs)


@pytest.fixture(scope="module")
def tabla():
    return read_table(str(TABLA))


@pytest.fixture(scope="module")
def salidas(tabla):
    return simulate(tabla)


@pytest.fixture(scope="module")
def salidas_invertidas(tabla):
    return simulate(tabla, invert=True)


# --- la tabla ---------------------------------------------------------------

def test_formato_archivo_tabla():
    lineas = TABLA.read_text().splitlines()
    assert len(lineas) == 16
    assert all(len(l) == 7 and set(l) <= {"0", "1"} for l in lineas)


def test_read_table_no_cae_en_tabla_cero(tabla):
    # read_table() devuelve 16 ceros si falla la lectura (sin lanzar error).
    assert len(tabla) == 16
    assert any(tabla), "read_table fallo: se obtuvo la tabla de ceros"


def test_patrones_distintos(tabla):
    assert len(set(tabla)) == 16


def test_decisiones_6_9_1(tabla):
    assert tabla[6] & seg_a_int("a"), "6 cerrado: enciende a"
    assert tabla[9] & seg_a_int("d"), "9 cerrado: enciende d"
    assert tabla[1] == seg_a_int("bc"), "1 a la derecha: b y c"


# --- el decodificador simulado (16 casos parametrizados) --------------------

@pytest.mark.parametrize("n, segs", GOLDEN.items())
def test_decodificador(n, segs, salidas):
    assert salidas[n] == seg_a_int(segs), f"entrada {n}"


@pytest.mark.parametrize("n, segs", GOLDEN.items())
def test_decodificador_invertido(n, segs, salidas_invertidas):
    assert salidas_invertidas[n] == (~seg_a_int(segs)) & 0x7F, f"entrada {n}"


# --- conversion a HDL (prueba de humo) --------------------------------------

@pytest.mark.parametrize("hdl, ext", [("VHDL", ".vhd"), ("verilog", ".v")])
def test_conversion_hdl(tabla, tmp_path, hdl, ext):
    convert(tabla, hdl=hdl, path=str(tmp_path))
    generado = tmp_path / f"sevensegdec_nexys{ext}"
    assert generado.exists() and generado.stat().st_size > 0
