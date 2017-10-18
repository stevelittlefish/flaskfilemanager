#!/bin/bash
PORT=8080

if [ ! -d env ]
then
	echo "Creating environment"
	virtualenv --python=python3 env
fi

./env/bin/pip install -r requirements.txt

rm out.log

echo
echo Starting on port $PORT
echo

./env/bin/gunicorn --bind 0.0.0.0:$PORT --threads=4 --workers=1 --reload --log-file ./out.log --worker-class=gthread $* wsgi:application

cat out.log

