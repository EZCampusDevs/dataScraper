#!/bin/sh

cd /home/data_scrape/py_core

alembic upgrade head

cd ..

python dscrape/__main__.py $*


