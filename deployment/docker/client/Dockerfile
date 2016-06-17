FROM ceejatec/ubuntu-1204-couchbase-cv

RUN pip install virtualenv
RUN virtualenv /lnt/venv

ADD deployment/docker/run.sh /run.sh
ADD . /lnt

RUN . /lnt/venv/bin/activate
RUN python /lnt/setup.py install
