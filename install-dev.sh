#!/bin/bash

# This script fails when any of its commands fail.
set -e

# Install non-pip dependencies
./installs/install-latex.sh
./installs/install-webpage.sh

# Install python dependencies
# On Mac OS, skip installing pytorch with CUDA because CUDA is not supported
if [[ $OSTYPE != 'darwin'* ]]; then
  # Manually install pytorch with `--no-cache-dir` to avoid pip getting killed: https://stackoverflow.com/a/54329850
  pip install torch==2.0.1 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir
fi
# Install all pinned dependencies
pip install -r requirements.txt
# upgrade pip to install in edit mode without setup.py
pip install --upgrade pip
# Install HELM in edit mode
pip install -e ".[all,dev]"
# Check dependencies
pip check