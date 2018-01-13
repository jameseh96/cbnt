from couchbase import CouchbaseTest


class KvEngineTest(CouchbaseTest):
    pass

def create_instance():
    return KvEngineTest()