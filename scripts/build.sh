#!/usr/bin/env sh

set -e

if [ ! -d "venv" ]; then
  virtualenv venv
fi

source venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt

pyinstaller remover.spec --clean -y
