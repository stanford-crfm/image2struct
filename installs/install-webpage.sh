#!/bin/bash

# This script fails when any of its commands fail.
set -e

# Install Jekyll dependencies
sudo apt-get install ruby-full build-essential zlib1g-dev

# Add environment variable to .bashrc
if ! grep -q "export GEM_HOME" ~/.bashrc; then
  echo "Adding GEM_HOME to .bashrc"
  echo "export GEM_HOME=$HOME/gems" >> ~/.bashrc
  echo "export PATH=$HOME/gems/bin:\$PATH" >> ~/.bashrc
  source ~/.bashrc
else
  echo "GEM_HOME already in .bashrc"
fi

# Install Jekyll
gem install jekyll bundler