FROM python:3-alpine

RUN addgroup data_scrape && adduser -D -G  data_scrape data_scrape

USER data_scrape

WORKDIR /home/data_scrape

ENV PATH="${PATH}:/home/data_scrape/.local/bin"

COPY ./dscrape ./dscrape
COPY ./py_core ./py_core
COPY ./requirements.txt .
COPY ./entrypoint.sh .

RUN pip install -r requirements.txt
RUN pip install -r ./py_core/requirements.txt

ENTRYPOINT ["/home/data_scrape/entrypoint.sh"]

