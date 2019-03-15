FROM couchbasebuild/server-ubuntu16-cv:20190315

# We need to export these environment variables
# as we are using a custom compiled version of GCC
ENV CC="/usr/local/bin/gcc"
ENV CXX="/usr/local/bin/g++"

RUN apt-get -y install python-dev

RUN sudo apt-get update && sudo apt-get -y install numactl build-essential autoconf libtool pkg-config python-opengl python-imaging python-pyrex python-pyside.qtopengl idle-python2.7 qt4-dev-tools qt4-designer libqtgui4 libqtcore4 libqt4-xml libqt4-test libqt4-script libqt4-network libqt4-dbus python-qt4 python-qt4-gl libgle3 python-dev
RUN sudo easy_install greenlet
RUN sudo easy_install gevent

RUN pip install virtualenv
RUN virtualenv /lnt/venv

ADD . /lnt

RUN . /lnt/venv/bin/activate
RUN python /lnt/setup.py install
