from couchbase import CouchbaseTest


class KvEngineSpockTest(CouchbaseTest):
    pass

def create_instance():
    return KvEngineSpockTest()