#!/bin/bash

source ./.venv/bin/activate
nohup python3 start.py >/dev/null 2>&1 &
