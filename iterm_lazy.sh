#!/bin/bash

rm *.plist
python3 extract.py $1 --template templates/iterm.plist
cp *.plist ~/Library/Application\ Support/iTerm2/DynamicProfiles/

# set macOS wallpaper
img_path="$(cd "$(dirname "$1")"; pwd)/$(basename "$1")"
cmd="tell application \"Finder\" to set desktop picture to POSIX file \"$img_path\""
echo "$cmd"
osascript -e "$cmd"

# This doesn't matter if the gvcci profile is set as default
sleep 3 # wait for iTerm to pick up the new profile before trying to load it
echo -e "\033]50;SetProfile=gvcci\a"

echo "If you want your iTerm color scheme to update automatically every"
echo "time you run this script, go to:"
echo "Preferences > Profiles > gvcci"
echo "Then under 'Other Actions...' select 'Set as Default'"
echo "This will take effect for all new terminal sessions"
