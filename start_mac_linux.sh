#!/bin/sh
cd "$(dirname "$0")" || exit 1
if [ -f config.local.json ]; then
  python3 app.py --config config.local.json
else
  python3 app.py
fi
