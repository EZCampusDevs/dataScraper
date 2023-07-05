#!/bin/sh

cd /opt

if [ -e './dscrape/env.sh' ] && [ -x './dscrape/env.sh' ]; then

    . ./dscrape/env.sh

fi

python ./dscrape/__main__.py $*


