#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seven segment decoder: script base del curso, modificado para usar pruebas
unitarias (pytest). La logica del decodificador vive aqui; las pruebas viven
en test_sevensegdec.py.

Cambios respecto a original/sevensegdec.py:
  * El testbench ya no compara contra la tabla (chequeo ad-hoc): solo genera
    los estimulos y entrega las salidas observadas.
  * simulate(): corre el testbench y devuelve la lista de salidas, para que
    las pruebas unitarias la inspeccionen.
  * convert(): la conversion a HDL se separo de run() para poder probarla.
La interfaz de linea de comandos (--simulation, --invert, --verilog, --table)
es la misma que la del script original.
"""

from myhdl import *
import argparse

# implementation (sin cambios)

@block
def sevensegdec(bcd: Signal, sseg: Signal, decod_table: tuple, invert: bool = False):
    """Seven segment decoder"""

    # internal signal for optional bit inversion
    ssegout = Signal(intbv(0)[7:])

    @always_comb
    def logic():
        """LUT implementation: based on a decoder table"""
        ssegout.next = decod_table[int(bcd)]

    @always_comb
    def invertproc():
        """Inverting process for output"""
        if invert:
            sseg.next = ~ssegout
        else:
            sseg.next = ssegout

    # this will include logic and invertproc
    return instances()


# testbench: solo estimulos, sin verificacion

@block
def sevensegdec_tb(decod_table: tuple, invert: bool = False,
                   results: list = None, verbose: bool = False):
    """Testbench for Seven segment decoder.

    Aplica cada valor de entrada y guarda la salida observada en `results`
    (si se entrega). La verificacion se hace en test_sevensegdec.py.
    """

    # Testbench signals
    bcd_tb = Signal(intbv(0)[4:])
    sseg_tb = Signal(intbv(0)[7:])

    uut = sevensegdec(bcd_tb, sseg_tb, decod_table, invert)

    @instance
    def stimulus():
        """Stimulus generation"""

        # run for each possible value
        for bcd_in in range(len(decod_table)):
            # stimulus input
            bcd_tb.next = bcd_in
            yield delay(10)

            sseg_readed = int(sseg_tb.val)
            if results is not None:
                results.append(sseg_readed)
            if verbose:
                print(f"({now()}) bcd={bcd_in:2d} -> sseg={sseg_readed:07b}")

    # this will include uut and stimulus
    return instances()


def simulate(decod_table: tuple, invert: bool = False, trace: bool = False,
             verbose: bool = False) -> list:
    """Corre el testbench y devuelve las salidas sseg observadas (una por entrada)."""
    results = []
    tb = sevensegdec_tb(decod_table, invert, results, verbose)
    tb.config_sim(trace=trace)  # trace=True genera sevensegdec_tb.vcd
    tb.run_sim(quiet=1)
    tb.quit_sim()
    return results


@block
def sevensegdec_nexys(bcd: Signal, sseg: Signal, bcdled: Signal, ssanodes: Signal, decod_table: tuple, invert: bool = False):
    """Envelope for running a demo in the Nexys4 DDR board for the Seven segment decoder"""

    # Main decoder instance
    ssdec = sevensegdec(bcd, sseg, decod_table, invert)

    @always_comb
    def logic():
        """Process to fill the LEDs for switches and display anodes"""
        bcdled.next = bcd
        ssanodes.next = intbv(0xfe)[8:] # only turn on first display, it is turned on with 0.

    # this will include ssdec and logic
    return instances()


def read_table(table_file: str) -> tuple:
    """Read the decoder table from text file:
        * Each line contains a string with 0s and 1s, in order "abcdefg"
        * It must contain 16 lines, one for each 4-bit digit
    """
    if table_file != "":
        try:
            with open(table_file) as f:
                return tuple([int(x, base=2) for x in f.readlines()])
        except Exception as ex:
            print(f"Exception reading the table: {ex}")
    return tuple([0 for x in range(16)])


def convert(table: tuple, hdl: str = "VHDL", path: str = ""):
    """Convierte sevensegdec_nexys a HDL (hdl = 'VHDL' o 'verilog')."""
    ss_sig = {
        "bcd": Signal(intbv(0)[4:]),
        "sseg": Signal(intbv(0)[7:]),
        "bcdled": Signal(intbv(0)[4:]),
        "ssanodes": Signal(intbv(0)[8:]),
        "invert": Signal(False),
        "decod_table": table
        }
    sscomponent = sevensegdec_nexys(**ss_sig)
    sscomponent.convert(hdl=hdl, path=path)


def run():
    """Entrypoint"""
    parser = argparse.ArgumentParser(description="Seven segment decoder")
    parser.add_argument(
        "--simulation",
        action="store_true",
        help="If enabled, run simulation in python",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert the outputs (simulation only)",
    )
    parser.add_argument(
        "--verilog",
        action="store_true",
        help="Convert to verilog instead of VHDL",
    )
    parser.add_argument(
        "--table",
        type=str,
        default="",
        help="Decoder table to include")
    args = parser.parse_args()

    if args.table != "":
        table = read_table(args.table)
    else:
        print("No table entered, put zero table by default.")
        table = read_table("")

    if args.simulation:
        # simulation
        simulate(table, args.invert, trace=True, verbose=True)
        print("Simulation done.")

    # conversion
    langout = "verilog" if args.verilog else "VHDL"
    convert(table, langout)
    print(f"Conversion done ({langout}).")


if __name__ == "__main__":
    run()
