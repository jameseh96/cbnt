import jenkins
import time
import sys

# BEFORE USE, INSERT USERNAME AND PASSWORD
server = jenkins.Jenkins("http://cv.jenkins.couchbase.com/", username="",
                         password="")

server.assert_node_exists("kv-engine-micro-bench-ubuntu1604")
server.disable_node("kv-engine-micro-bench-ubuntu1604",
                    "Running automatic backup and update, back online soon!")

cv_perf_info = server.get_job_info("kv-engine-cv-perf")
master_perf_info = server.get_job_info("kv-engine-master-perf")

while ((cv_perf_info['lastBuild']['number'] !=
        cv_perf_info['lastCompletedBuild']['number']) or
       (master_perf_info['lastBuild']['number'] !=
        master_perf_info['lastCompletedBuild']['number'])):
    print("Build(s) still running, retrying in 15s")
    time.sleep(15)
    cv_perf_info = server.get_job_info("kv-engine-cv-perf")
    master_perf_info = server.get_job_info("kv-engine-master-perf")

sys.exit(0)
