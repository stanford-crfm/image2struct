#!/bin/bash

# This script fails when any of its commands fail.
set -e

# Install LaTeX
sudo apt-get install texlive-latex-extra texlive-fonts-recommended texlive-science
sudo apt-get install latexmk