#!/bin/bash

# This script fails when any of its commands fail.
set -e

# Install Jekyll dependencies
sudo apt-get install ruby-full build-essential zlib1g-dev

# Check if running in GitHub Actions
if [ "$GITHUB_ACTIONS" != "true" ]; then
  # Add environment variable to .bashrc if not running on GitHub Actions
  if ! grep -q "export GEM_HOME" ~/.bashrc; then
    echo "Adding GEM_HOME to .bashrc"
    echo "export GEM_HOME=$HOME/gems" >> ~/.bashrc
    echo "export PATH=$HOME/gems/bin:\$PATH" >> ~/.bashrc
    # Note: `source` won't work as expected because it affects only the current shell session
    # Consider running this script with `source` or manually sourcing .bashrc afterwards
  else
    echo "GEM_HOME already in .bashrc"
  fi
else
  # Directly export variables when running in GitHub Actions
  echo "Running in GitHub Actions, exporting variables directly"
  export GEM_HOME=$HOME/gems
  export PATH=$HOME/gems/bin:$PATH
fi

# Install Jekyll
gem install jekyll bundler
