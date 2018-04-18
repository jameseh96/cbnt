import jenkins

# BEFORE USE, INSERT USERNAME AND PASSWORD
server = jenkins.Jenkins("http://cv.jenkins.couchbase.com/", username="",
                         password="")

server.enable_node("kv-engine-micro-bench-ubuntu1604")
