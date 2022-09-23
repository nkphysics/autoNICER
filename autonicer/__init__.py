from . import autonicer
from .autonicer import AutoNICER
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

    args = p.parse_args()
    an = autonicer.AutoNICER(args.src)
    an.call_nicer()
    an.command_center()
