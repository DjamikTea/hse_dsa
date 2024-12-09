#!/bin/bash

VENV_PATH=".venv"
python3 -m venv $VENV_PATH

$VENV_PATH/bin/pip install -U pip setuptools --break-system-packages
$VENV_PATH/bin/pip install poetry --break-system-packages

poetry build
