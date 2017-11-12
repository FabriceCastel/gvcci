#!/bin/bash

python3 src/extract.py --template templates/iterm.plist "$1"
img_name="$(basename "$1" | cut -d'.' -f1)"
./gvcci-apply/apply.sh $img_name iterm
