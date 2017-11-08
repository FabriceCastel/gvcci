import argparse
import os
import sys
import json

class Argument:
	def __init__(self, name, help, dest, default=None):
		self.name = name
		self.help = help
		self.default = default
		self.dest = dest

	def add_to_parser(self, parser):

		# the first param for a positional argument is considered to be the dest so you
		# don't need to pass it in as a named param
		if (self.name[:2] != "--"):
			parser.add_argument(
				self.name,
				default=self.default,
				help=self.help,
				nargs="+"
			)
		elif (self.default == None):
			parser.add_argument(
				self.name,
				dest=self.dest,
				help=self.help,
				type=str
			)
		else:
			parser.add_argument(
				self.name,
				default=self.default,
				dest=self.dest,
				help=self.help,
				type=str
			)

arguments = [
	Argument(
		name="images",
		help="The images to generate color themes for.",
		dest="images"
	),
	Argument(
		name="--background",
		help="[dark|light|<#hex_code>] specify whether the script should generate a light/dark theme or use a specific hex color for the background.",
		default="auto",
		dest="background"
	),
	Argument(
		name="--template",
		help="Template or directory of templates to use for the theme.",
		default="./templates/",
		dest="template_path"
	),
	Argument(
		name="--config",
		help="Config file to use. Config settings will override other commandline params.",
		dest="config_path"
	)
]

def get_args():
	parser = argparse.ArgumentParser(description="Create terminal themes to match wallpaper images.")

	for argument in arguments:
		argument.add_to_parser(parser)

	args = vars(parser.parse_args())
	config_path = args['config_path']

	if (config_path != None):
		with open(os.path.realpath(config_path), 'r') as config_json:
			config = json.load(config_json)
			for key, value in config.items():
				args[key] = value

	return args

