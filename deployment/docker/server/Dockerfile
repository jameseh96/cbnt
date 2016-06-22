FROM python:2.7

EXPOSE 8000

RUN pip install virtualenv
RUN virtualenv /lnt/venv

ADD deployment/docker/server/run.sh /run.sh
ADD . /lnt

RUN . /lnt/venv/bin/activate
RUN pip install sphinx
RUN pip install sphinx_bootstrap_theme

RUN make -C /lnt/docs
RUN python /lnt/setup.py install

RUN chmod +x /run.sh
CMD /run.sh