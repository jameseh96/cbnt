#!/usr/bin/env bash
set -x
set -e
PROJECT=$1
NUM_COMMITS=$2
cd ep-engine
git fetch http://review.couchbase.org/ep-engine refs/changes/05/65005/9
cd ../memcached
git fetch http://review.couchbase.org/memcached refs/changes/09/65009/2
cd "../$PROJECT"
GIT_LOG=$(git --no-pager log --pretty=format:"%H~%cd" -n $NUM_COMMITS --reverse; echo)
IFS=$'\n';
cd ..
for OUTPUT in $GIT_LOG; do
repo sync -j24 -d
cd ep-engine
export GERRIT_PATCHSET_REVISION=$(echo $OUTPUT | cut -f1 -d'~');
COMMIT_DATE=$(echo $OUTPUT | cut -f2 -d'~');
cd ..
repo forall -c 'git checkout `git rev-list HEAD -n1 --before=$COMMIT_DATE`'
cp -f tlm/CMakeLists.txt tlm/Makefile tlm/GNUmakefile .
cd "$PROJECT"
export GERRIT_CHANGE_COMMIT_MESSAGE=$(python -c "import base64, sys; print base64.b64encode(sys.argv[1])" "$(git show ${GERRIT_PATCHSET_REVISION} --no-patch --format=%B)")
cd ../ep-engine
if ! git merge-base --is-ancestor a10dd01bfcd4d2a46a5a55238a4caeecd999c322 HEAD 2> /dev/null;
then git cherry-pick -n a10dd01bfcd4d2a46a5a55238a4caeecd999c322;
fi
cd ../memcached
if ! git merge-base --is-ancestor b40a4577861c79ea1a4f5f5f3f84353ab7b46679 HEAD 2> /dev/null;
then git cherry-pick -n b40a4577861c79ea1a4f5f5f3f84353ab7b46679;
fi
cd ..
make -j24
CBNT_MACHINE_NAME="KV-Engine-Perf-1" lnt runtest "$PROJECT" /home/couchbase/cbnt_config.yml master --submit_url=http://172.23.122.48/submitRun -v --commit=1 --iterations=5
make clean -j24
done