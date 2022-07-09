from . import autonicer
from .autonicer import AutoNICER
import click

@click.command(context_settings={"help_option_names": ["-h", "--help"]},
				help="A program for piplining NICER data reduction. Run by just typing autonicer.")
@click.option("--src", 
				type = str, 
				default = None,
				help = "Option to set the src from the command line")
@click.option("-inobs", "--inobs",
				type=click.Path(
				exists=True, file_okay=True, dir_okay=True, readable=True, allow_dash=True
    			),
				default = None,
				help = "Input of OBSID directory or output log from previous autonicer run")

def run(src, inobs):
	an = autonicer.AutoNICER(src, inobs)
	an.call_nicer()
	an.command_center()
