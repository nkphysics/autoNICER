from .autonicer import AutoNICER
from .autonicer import get_caldb_ver
from .reprocess import reprocess_check
from .reprocess import inlist
from .reprocess import Reprocess
import argparse as ap


def run(args=None):
    p = ap.ArgumentParser(
        description="A program for piplining NICER data reduction. Run by just typing autonicer."
    )

    p.add_argument(
        "-src",
        "--src",
        help="Set the src from the command line",
        type=str,
    )

    p.add_argument(
        "-checkcal",
        "--checkcal",
        help="Checks if mpu7_cl.evt are up to date with latest NICER calibrations",
        action="store_true",
        default=False,
    )

    p.add_argument(
        "-reprocess",
        "--reprocess",
        help="Engages a reprocessing of calibrations ",
        action="store_true",
        default=False,
    )

    p.add_argument(
        "-bc",
        "--bc",
        help="Engages option for a barycenter correction in data reduction procedure",
        action="store_true",
        default=None,
    )

    p.add_argument(
        "-compress",
        "--compress",
        help="Engages option for .gz compression of ufa.evt files",
        action="store_true",
        default=None,
    )

    p.add_argument(
        "-i",
        "-inlist",
        "--inlist",
        help="Input .csv list with path to OBSID dirs or mpu7_cl.evt files for use with --reprocess and/or --checkcal",
        default=None,
        nargs="+",
    )

    argp = p.parse_args(args)
    if argp.checkcal is True or argp.reprocess is True:
        if argp.inlist is None:
            reprocess_check(argp)
        else:
            inlist(argp)
    else:
        an = autonicer.AutoNICER(argp.src, argp.bc, argp.compress)
        an.call_nicer()
        an.command_center()
