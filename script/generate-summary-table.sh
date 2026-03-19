#!/bin/bash
set -xe

python3 -m venv .venv
.venv/bin/python -m pip install -r script/requirements.txt \
  --quiet --disable-pip-version-check
.venv/bin/python script/generate-summary-table.py $1
