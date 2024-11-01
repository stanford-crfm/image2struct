#!/bin/bash

# Source: https://github.com/stanford-crfm/helm/blob/main/pre-commit.sh

# This script fails when any of its commands fail.
set -e

# Check that python version is at least 3.8.
valid_version=$(python3 -c 'import sys; print(sys.version_info[:2] >= (3, 8))')
if [ "$valid_version" == "False" ]; then
  echo "Python 3 version (python3 --version) must be at least 3.8, but was:"
  echo "$(python3 --version 2>&1)"
  exit 1
fi

# Python style checks and linting
black --check --diff src || (
  echo ""
  echo "The code formatting check failed. To fix the formatting, run:"
  echo ""
  echo ""
  echo -e "\tblack src"
  echo ""
  echo ""
  exit 1
)

mypy --install-types --non-interactive src
flake8 src

echo "Done."