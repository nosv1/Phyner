#!/bin/sh

restart=1
while [[ 1 -eq ${restart} ]]; do
	restart=0

	echo "git pull"
	git pull
	echo

	echo "python3 Controller.py"
	restart=$(python3 Controller.py | tail -n 1)
	restart=$((restart+0))
	echo
done;
