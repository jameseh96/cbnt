FROM ceejatec/ubuntu-1204-couchbase-cv

RUN sudo apt-get update && sudo apt-get -y install numactl

RUN pip install virtualenv
RUN virtualenv /lnt/venv

ADD 1204 /lnt

RUN . /lnt/venv/bin/activate
RUN python /lnt/setup.py install
