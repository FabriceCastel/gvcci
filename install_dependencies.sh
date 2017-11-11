#!/bin/bash

echo "Installing python library dependencies..."
pip3 install cython pystache numpy scikit-learn scikit-image

echo "Initializing git submodules..."
git submodule init

echo "Updateing git submodules..."
git submodule update --remote --merge
