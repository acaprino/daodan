from vend_demo._vendor import tinyjson
from vend_demo.proto import events_pb2


def parse(raw):
    return events_pb2.Event(id=tinyjson.loads(raw)["id"])
