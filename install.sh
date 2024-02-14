#!/bin/bash

# This script fails when any of its commands fail.
set -e

# Install non-pip dependencies
sudo sh ./installs/install-latex.sh
sudo sh ./installs/install-webpage.sh