#!/usr/bin/env bash
set -e

if [ $# -eq 0 ]; then
    echo "Usage: replay-history.sh"
    echo "-n --num-commits     number of commits to replay"
    echo "-s --start-commit    SHA of commit to start from"
    echo "-h --help            show this help message"
    exit 1
fi

for i in "$@"
do
case $i in
    -n=*|--num-commits=*)
    NUM_COMMITS="${i#*=}"
    shift # past argument=value
    ;;
    -s=*|--start-commit=*)
    START_COMMIT="${i#*=}"
    shift # past argument=value
    ;;
    -h|--help)
    echo "Usage: replay-history.sh"
    echo "-n --num-commits     number of commits to replay"
    echo "-s --start-commit    SHA of commit to start from"
    echo "-h --help            show this help message"
    shift # past argument=value
    exit 1
    ;;
    *)
    echo "Unknown flag set ${i}"
    exit 1
          # unknown option
    ;;
esac
done

if [ -z ${NUM_COMMITS+x} ]; then
    echo "Number of commits not specified";
    exit 1
else
    echo "Replaying the last $NUM_COMMITS commits";
fi

set -x

mkdir source
cd source
repo init -u git://github.com/couchbase/manifest -m branch-master.xml
repo sync

cd kv_engine
git fetch http://review.couchbase.org/kv_engine refs/changes/42/87842/5
if [ -z ${START_COMMIT+x} ]; then
    echo "Checking out $START_COMMIT"
    git checkout $START_COMMIT
fi
GIT_LOG=$(git --no-pager log --pretty=format:"%H~%cd" -n $NUM_COMMITS --reverse; echo)
IFS=$'\n';
cd ..

for OUTPUT in $GIT_LOG; do
    repo sync -j24 -d
    cd kv_engine
    export GERRIT_PATCHSET_REVISION=$(echo $OUTPUT | cut -f1 -d'~');
    COMMIT_DATE=$(echo $OUTPUT | cut -f2 -d'~');
    cd ..
    repo forall -c 'git checkout `git rev-list HEAD -n1 --before=$COMMIT_DATE`'
    cp -f tlm/CMakeLists.txt tlm/Makefile tlm/GNUmakefile .
    cd kv_engine
    export GERRIT_CHANGE_COMMIT_MESSAGE=$(python -c "import base64, sys; print base64.b64encode(sys.argv[1])" "$(git show ${GERRIT_PATCHSET_REVISION} --no-patch --format=%B)")
    if ! git merge-base --is-ancestor 7119049b4afa963e12b97cc172f6ba30e664eec1 HEAD 2> /dev/null;
        then git cherry-pick -n 7119049b4afa963e12b97cc172f6ba30e664eec1;
    fi
    cd ..
    make -j24
    CBNT_MACHINE_NAME="KV-Engine-Perf-2" lnt runtest "kv-engine" kv_engine/tests/cbnt_tests/cbnt_test_list.yml master --submit_url=http://172.23.122.48/submitRun -v --commit=1 --iterations=5
    make clean -j24
done

cd ..
rm -rf source