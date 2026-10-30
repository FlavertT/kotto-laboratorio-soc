#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
exec unshare --user --map-root-user --net sh -c 'ip link set lo up; exec .venv/bin/python -m lab.experiment "$@"' sh "$@"
