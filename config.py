import argparse
import os
import sys
import json


def get_args():
	parser = argparse.ArgumentParser(description="Create terminal themes to match wallpaper images.")

	parser.add_argument(
		"images",
		help="The images to generate color themes for.",
		nargs="+"
	)

	parser.add_argument(
		"--background",
		help="[dark|light|<#hex_code>] specify whether the script should generate a light/dark theme or use a specific hex color for the background.",
		default="auto",
		dest="background",
		type=str
	)

	parser.add_argument(
		"--template",
		help="Template or directory of templates to use for the theme.",
		default="./templates/",
		dest="template_path",
		type=str
	)

	parser.add_argument(
		"--config",
		help="Config file to use. Config settings will override other commandline params.",
		dest="config_path",
		type=str
	)

	args = vars(parser.parse_args())
	config_path = args['config_path']

	if (config_path != None):
		with open(os.path.realpath(config_path), 'r') as config_json:
			config = json.load(config_json)
			for key, value in config.items():
				args[key] = value

	return args
