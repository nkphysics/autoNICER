from .autonicer import AutoNICER
from .reprocess import checkcal
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
        "-force",
        "--force",
        help="Forces a reprocess if calibrations are not up to date with latest CALDB",
        action="store_true",
        default=False,
    )

    args = p.parse_args()
    if args.checkcal == True:
        checkcal()

    else:
        an = autonicer.AutoNICER(args.src)
        an.call_nicer()
        an.command_center()
