FROM python:3.10

WORKDIR /opt/django_etl_panel

COPY requirements.txt requirements.txt

RUN  pip install --upgrade pip \
     && pip install -r requirements.txt --no-cache-dir

COPY movies.sqlite movies.sqlite

COPY ./src .

EXPOSE 8000

COPY script.sh /

RUN chmod +x /script.sh

ENTRYPOINT ["/script.sh"] 
