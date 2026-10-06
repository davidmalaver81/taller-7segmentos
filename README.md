# Taller segundo corte — Decodificador de 7 segmentos

Archivos: `tabla.txt`, `original/sevensegdec.py` (script base del curso, sin modificar), `sevensegdec.py` (versión modificada), `test_sevensegdec.py` (pytest), `hdl/` (HDL generado), `sevensegdec_tb.vcd` y capturas en `img/`.

## 1. Tabla de decodificación (orden `abcdefg`, 1 = encendido)

| N | Bits | Dibujo | Segmentos |
|---|------|--------|-----------|
| 0 | 1111110 | 0 | abcdef |
| 1 | 0110000 | 1 (derecha) | bc |
| 2 | 1101101 | 2 | abdeg |
| 3 | 1111001 | 3 | abcdg |
| 4 | 0110011 | 4 | bcfg |
| 5 | 1011011 | 5 | acdfg |
| 6 | 1011111 | 6 cerrado | acdefg |
| 7 | 1110000 | 7 | abc |
| 8 | 1111111 | 8 | abcdefg |
| 9 | 1111011 | 9 cerrado | abcdfg |
| 10 | 0000001 | `-` | g |
| 11 | 0001000 | `_` | d |
| 12 | 1000000 | `‾` | a |
| 13 | 1100011 | `°` | abfg |
| 14 | 1001001 | `≡` | adg |
| 15 | 1111000 | `]` | abcd |

### Decisiones para 0–9
- **6 cerrado:** enciende el segmento superior `a`, así se distingue claramente del dígito `b`/otros símbolos y queda simétrico con el 9.
- **9 cerrado:** enciende el segmento inferior `d`, por la misma razón de simetría con el 6.
- **1 a la derecha:** usa `b` y `c`, el lado más habitual y el que mantiene alineados los dígitos al escribir números de varias cifras.

### Símbolos propios para 10–15 (sin letras A–F)
- **10 `-`:** solo `g`, un guion (signo menos / "vacío en medio").
- **11 `_`:** solo `d`, guion bajo, es el opuesto vertical del guion.
- **12 `‾`:** solo `a`, sobrerraya, completa la familia de una sola barra horizontal.
- **13 `°`:** `abfg`, el cuadrito superior parece un símbolo de grado.
- **14 `≡`:** `adg`, las tres barras horizontales forman el símbolo de equivalencia.
- **15 `]`:** `abcd`, un corchete derecho, la mitad derecha del 0.

Los 16 patrones son distintos entre sí (verificado en `test_formato_tabla`/`test_patrones_distintos`).

## 2. Comandos usados

```bash
pip install myhdl pytest

# Simulación + generación de VHDL (por defecto), con el script base del curso
python original/sevensegdec.py --simulation --table tabla.txt

# Alternativa: Verilog
python original/sevensegdec.py --simulation --table tabla.txt --verilog

# Pruebas unitarias (script modificado)
pytest -v
```
> Pega aquí el comando **exacto** que ejecutaste. Los archivos se crean en el directorio actual: `sevensegdec_nexys.vhd` (o `.v`), `pck_myhdl_011.vhd` (solo VHDL) y `sevensegdec_tb.vcd`. Verifica los nombres con `ls` y muévelos a `hdl/`.

## 3. Simulación

Salida (pegar aquí la salida real de tu terminal):

```
Simulation done.
Conversion done (VHDL).
```

**Qué verifica el testbench.** `sevensegdec_tb` recorre las 16 entradas de `bcd` (0 a 15), espera 10 unidades de tiempo en cada una para que la lógica combinacional se estabilice, lee `sseg` y lo compara con la entrada correspondiente de la tabla (`decod_table[bcd]`).

**Por qué no aparecen mensajes de ERROR.** El testbench solo imprime `ERROR` cuando la salida leída difiere de la tabla. El diseño sale de esa misma tabla, así que con una tabla bien leída ambas coinciden en las 16 entradas y no se imprime nada: el silencio significa que pasó. Es un chequeo débil porque compara la tabla consigo misma: no detecta una tabla con patrones equivocados, y con `--invert` el testbench original imprimiría errores en todas las entradas, ya que compara contra la tabla sin invertir. Por eso se migró a pruebas unitarias con valores esperados independientes (sección 5).

**Qué representan los 7 bits de `sseg`.** Un bit por segmento en orden `abcdefg`: `a` es el MSB (bit 6) y `g` el LSB (bit 0). Un 1 enciende el segmento (lógica positiva; con `--invert` se invierte para displays de lógica negativa). Ejemplo: `0110000` = segmentos b y c = "1".

### Cómo leer el VCD (GTKWave / vc.drom.io)
1. Abre `sevensegdec_tb.vcd` y agrega `bcd_tb` y `sseg_tb`.
2. Muestra `bcd_tb` en decimal y `sseg_tb` en binario.
3. Observa 16 escalones de 10 unidades de tiempo: `bcd_tb` sube de 0 a 15 y `sseg_tb` cambia al mismo tiempo (como mucho un delta de simulación), sin reloj, porque es lógica combinacional.
4. Comprueba 3 casos con tu tabla (por ejemplo `bcd=1` → `0110000`, `bcd=6` → `1011111`, `bcd=15` → `1111000`) y adjunta una captura de cada uno.

## 4. HDL generado
Ver `hdl/sevensegdec_nexys.vhd` (o `.v`). El diseño convertido es `sevensegdec_nexys`: envuelve al decodificador y además conecta `bcd` a `bcdled` (LEDs) y fija `ssanodes = 11111110` para encender solo el primer display de la Nexys4 DDR.

**De LUT a lógica combinacional.** `ssegout.next = decod_table[int(bcd)]` se convierte en un proceso sensible solo a `bcd` con una estructura `case`/tabla: cada entrada de la tabla es una rama que asigna un patrón de 7 bits. Un segundo proceso combinacional aplica la inversión según `invert`. No hay reloj ni registros: el sintetizador toma esa tabla de verdad y cada bit de `sseg` queda como una función booleana de los 4 bits de `bcd` (una LUT de 4 entradas en la FPGA).
> Revisa tu archivo generado y ajusta esta explicación a lo que realmente ves en él.

## 5. Pruebas unitarias
`test_sevensegdec.py` usa **pytest** sobre `sevensegdec.py` (versión modificada). Cambios respecto al original: el testbench ya no compara contra la tabla, solo genera estímulos y devuelve las salidas (`simulate()`), y la conversión a HDL se separó en `convert()`. Las pruebas:
- parametrizan los **16 casos** con `@pytest.mark.parametrize` (normal e invertido), comparando contra segmentos esperados escritos a mano;
- verifican el formato de `tabla.txt`, que los 16 patrones sean distintos y las decisiones de 6, 9 y 1;
- detectan que `read_table` no haya devuelto la tabla de ceros (el script la devuelve en silencio si falla la lectura);
- hacen una prueba de humo de la conversión a VHDL y Verilog.
