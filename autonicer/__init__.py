from .autonicer import AutoNICER
from .reprocess import Reprocess
import argparse as ap


def run():
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

    args = p.parse_args()
    if args.checkcal == True and args.reprocess == True:
        check = Reprocess()
        check.checkcal()
    elif args.checkcal == True:
        check = Reprocess()
        check.checkcal()
    elif args.reprocess == True:
        pass
    else:
        an = autonicer.AutoNICER(args.src)
        an.call_nicer()
        an.command_center()
