from couchbase import CouchbaseTest


class MemcachedTest(CouchbaseTest):
    pass

def create_instance():
    return MemcachedTest()