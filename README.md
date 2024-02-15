# Image2Structure - Data collection

This repository contains the data collection for the Image2Structure project.

## Installation
To install the package, you can use pip:

    pip install -e ".[all]"

Some formats require additional dependencies. To install all dependencies, use:

    sudo ./install-dev.sh


# Contributing
To contribute to this project, install the dependencies and git hook scripts:

    ./pre-commit.sh && pre-commit install

To run unit tests:

    python -m pytest