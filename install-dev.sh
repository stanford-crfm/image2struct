#!/bin/bash

# This script fails when any of its commands fail.
set -e

# Install non-pip dependencies
sudo sh ./install.sh

# Install python dependencies
# On Mac OS, skip installing pytorch with CUDA because CUDA is not supported
if [[ $OSTYPE != 'darwin'* ]]; then
  # Manually install pytorch with `--no-cache-dir` to avoid pip getting killed: https://stackoverflow.com/a/54329850
  pip install torch==2.0.1+cu117 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cu117 --no-cache-dir
fi
# Install all pinned dependencies
pip install -r requirements.txt
# upgrade pip to install in edit mode without setup.py
pip install --upgrade pip
# Install HELM in edit mode
pip install -e ".[all,dev]"
# Check dependencies
pip check

# Create a cache dir for Mypy
# See: https://github.com/python/mypy/issues/10768
mkdir -p .mypy_cache