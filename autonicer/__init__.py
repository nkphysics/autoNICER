from . import autonicer
from .autonicer import AutoNICER
import click

@click.command(context_settings={"help_option_names": ["-h", "--help"]},
				help="A program for piplining NICER data reduction. Run by just typing autonicer.")
@click.option("--src", 
				type = str, 
				default = None,
				help = "Option to set the src from the command line")
#@click.option("--reprocess",
#				is_flag = True,
#				help = "Navigate to OBSID directory and issue --reprocess to reprocess the OBSID dataset with new commands/calibrations")

def run(src):
	an = autonicer.AutoNICER(src)
	an.call_nicer()
	an.command_center()
