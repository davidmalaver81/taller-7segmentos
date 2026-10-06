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

Comando: `python original/sevensegdec.py --simulation --table tabla.txt`

Salida (también guardada en [`salida_simulacion.txt`](salida_simulacion.txt)):

```
<class 'myhdl.StopSimulation'>: No more events
Simulation done.
Conversion done (VHDL).
```

La primera línea es el aviso normal de MyHDL al terminar: el testbench recorrió las 16 entradas y no quedan más eventos. No aparece ningún `ERROR`, lo que indica que `sseg` coincidió con la tabla en los 16 casos.

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
Ver [`hdl/sevensegdec_nexys.vhd`](hdl/sevensegdec_nexys.vhd) (generado con MyHDL 0.11.52).

**Interfaz.** La entidad `sevensegdec_nexys` tiene como entradas `bcd` (4 bits) e `invert`, y como salidas `sseg` (7 bits), `bcdled` (4 bits) y `ssanodes` (8 bits). `invert` era un parámetro en la simulación, pero en el HDL es un puerto de entrada (en la Nexys4 DDR se puede conectar a un interruptor).

**De LUT a lógica combinacional.**
- `decod_table[int(bcd)]` se convirtió en el proceso `sevensegdec1_logic`, sensible únicamente a `bcd`. Contiene un `case to_integer(bcd)` con una rama por cada línea de `tabla.txt`; la última (entrada 15) se emite como `when others`.
- No hay reloj ni registros: la salida depende solo de la entrada actual. Por eso es lógica combinacional, y cada bit de `ssegout` es una función booleana de los 4 bits de `bcd`. Una herramienta de síntesis la implementa como una LUT de 4 entradas por bit.
- El proceso `sevensegdec1_invertproc` (sensible a `ssegout` e `invert`) deja pasar la señal tal cual o la niega con `not`, según `invert`.
- `bcdled <= bcd` copia la entrada a los LEDs y `ssanodes <= to_unsigned(254, 8)` fija `11111110`: solo se enciende el primer display, porque los ánodos se activan con 0.

## 5. Pruebas unitarias
`test_sevensegdec.py` usa **pytest** sobre `sevensegdec.py` (versión modificada). Cambios respecto al original: el testbench ya no compara contra la tabla, solo genera estímulos y devuelve las salidas (`simulate()`), y la conversión a HDL se separó en `convert()`. Las pruebas:
- parametrizan los **16 casos** con `@pytest.mark.parametrize` (normal e invertido), comparando contra segmentos esperados escritos a mano;
- verifican el formato de `tabla.txt`, que los 16 patrones sean distintos y las decisiones de 6, 9 y 1;
- detectan que `read_table` no haya devuelto la tabla de ceros (el script la devuelve en silencio si falla la lectura);
- hacen una prueba de humo de la conversión a VHDL y Verilog.
