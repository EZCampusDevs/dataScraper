FROM python:3-alpine

ARG DIR="/opt/dscrape"

RUN mkdir $DIR

COPY ./dscrape $DIR
COPY ./py_core $DIR/../py_core
COPY ./requirements.txt $DIR
COPY ./entrypoint.sh $DIR

COPY .env $DIR

RUN pip install -r $DIR/requirements.txt

# have to hard code path here???
ENTRYPOINT ["/opt/dscrape/entrypoint.sh"]

