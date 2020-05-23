#!/usr/bin/env sh

set -e

if type virtualenv > /dev/null 2>&1; then
  echo 'virtualenv...OK'
else
  pip3 install virtualenv
fi

if [ ! -d "venv" ]; then
  virtualenv venv
fi

venv/bin/pip install -r requirements.txt
venv/bin/pip install -r requirements-dev.txt

venv/bin/pyinstaller remover.spec --clean -y
