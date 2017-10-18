#!/bin/bash
if [ ! -d env ]
then
	echo "Creating environment"
	virtualenv --python=python3 env
fi

./env/bin/pip install -r requirements.txt

