import argparse
import os
import sys
import json

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
	"--print-output",
	help="Print the resulting template output to stdout.",
	dest="print_output",
	action='store_true'
)
parser.set_defaults(print_output=False)

parser.add_argument(
	"--symlink-wallpaper",
	help="When saving the wallpaper in ~/.gvcci/themes/ use a symlink rather than copy the file.",
	dest="symlink_wallpaper",
	action='store_true'
)
parser.set_defaults(symlink_wallpaper=False)


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

def get_args():
	return args

