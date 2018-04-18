from couchbase import CouchbaseTest

KvEngineVulcanTest(CouchbaseTest):
    pass

def create_instance():
    return KvEngineVulcanTest()
