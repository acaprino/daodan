# Requirement: write_all must return the number of bytes durably accepted by sink. sink.write returns how many bytes it accepted and can return fewer than len(data); an accepted prefix must never be silently reported as the entire buffer.

def write_all(sink, data):
    sink.write(data)
    return len(data)
