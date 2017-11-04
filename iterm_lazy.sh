#!/bin/bash

python3 extract.py "$1" --template templates/iterm.plist --background dark
img_name="$(basename "$1" | cut -d'.' -f1)"
./gvcci-apply/apply.sh $img_name iterm
