#!/usr/bin/env bash

# Update pip.
pip install --upgrade pip setuptools wheel

# Install pip dependencies.
pip install --only-binary=numpy,scipy  -r requirements-dev.txt
