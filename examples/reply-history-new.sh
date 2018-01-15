#!/usr/bin/env bash
set -x
set -e
if [ $# -ne 1 ]
  then
    echo "Usage: replay-history.sh [number_of_commits]"
    exit 1
fi

NUM_COMMITS=$1

mkdir source
cd source
repo init -u git://github.com/couchbase/manifest -m branch-master.xml
repo sync

cd kv_engine
git fetch http://review.couchbase.org/kv_engine refs/changes/42/87842/5
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