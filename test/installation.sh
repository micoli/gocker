#!/bin/bash

export POETRY_VERSION=1.2.0
export POETRY_HOME=/opt/poetry
export POETRY_VENV=/opt/poetry-venv
export POETRY_CACHE_DIR=/opt/.cache

python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

export PATH="${PATH}:${POETRY_VENV}/bin"

pip install --upgrade --force-reinstall git+https://github.com/micoli/gocker.git

gocker --action shortcut-list
