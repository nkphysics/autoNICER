from . import autonicer

def run():
	an = autonicer.AutoNICER()
	an.call_nicer()
	an.command_center()
	an.pull_reduce()
