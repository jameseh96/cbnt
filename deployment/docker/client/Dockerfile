FROM ceejatec/ubuntu-1204-couchbase-cv

RUN pip install virtualenv
RUN virtualenv /lnt/venv

ADD 1204 /lnt

RUN . /lnt/venv/bin/activate
RUN python /lnt/setup.py install
