# GVCCI

## About

This project was developed as an alternative to the commonly used tool ```wal``` which was used by many in the UNIX community to extract colors from images in order to create terminal themes that matched their wallpapers.

The main flaw with ```wal``` is that it often missed smaller pops of differentiated color within an image, leaving its results monotone & uninteresting. This project aims to remedy that by using clustering algorithms on an image's colours so that small pockets of highly differentiated colours get picked up and have a shot at making it into the final colour palette.

For some examples, check out: http://fabricecastel.github.io/colors/examples.html

The project is still very much a work in progress, with background color logic in the works so that you can choose between light, dark & custom background colors. Feel free to join in the discussion via the github issues page, or the thread on /r/unixporn [here](https://www.reddit.com/r/unixporn/comments/77iagc/writing_a_new_tool_to_extract_terminal_colour/)

## Setup

This program has the following dependencies:

* python3
* numpy
* scikit-learn
* scikit-image
* hasel

To setup standard dependencies:

1. Download and install Python 3: https://www.python.org/downloads/ (3.6.3 is the most up to date version as of the writing of this readme)
2. ```pip3 install cython numpy scikit-learn scikit-image```

To setup the project:

1. Download & Extract (or clone) the source files from the github repo: https://github.com/FabriceCastel/gvcci
2. run ```python3 setup.py install``` to install the hasel dependency in the directory colorizer-terminator
3. run ```python3 extract.py path/to/image.jpg``` to run the program

Running the program will print the generated color palette and generate an html file with some previews that you can open in any web browser.

## Options

`--background [auto|light|dark|<hex>]`

`--background` defaults to `auto`, which can pick either a light or dark background depending on the image. the `light` and `dark` options have it pick either a light or a dark color from the image as the background, and `<hex>` allows you to specify a hex code to use as background color.
