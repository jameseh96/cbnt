FROM couchbasebuild/server-ubuntu16-cv:20200211

#WARNING: This Dockerfile needs to be built from within the cbnt git repo to ensure it can acess /lnt and requirements.txt
# Also 

# We need to export these environment variables
# as we are using a custom compiled version of GCC
ENV CC="/usr/local/bin/gcc"
ENV CXX="/usr/local/bin/g++"

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y auto-remove
RUN apt-get -y install numactl build-essential autoconf libtool pkg-config python-opengl python-imaging python-pyrex python-pyside.qtopengl idle-python2.7 qt4-dev-tools qt4-designer libqtgui4 libqtcore4 libqt4-xml libqt4-test libqt4-script libqt4-network libqt4-dbus python-qt4 python-qt4-gl libgle3 libpq-dev

RUN pip install --upgrade pip
RUN pip install virtualenv

RUN virtualenv /lnt/venv
ADD . /lnt
RUN . /lnt/venv/bin/activate

RUN pip install -r /lnt/requirements.txt
RUN python /lnt/setup.py install
