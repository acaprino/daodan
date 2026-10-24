# Requirement: write_all must return the number of bytes durably accepted by sink. sink.write returns how many bytes it accepted and can return fewer than len(data); an accepted prefix must never be silently reported as the entire buffer.

def write_all(sink, data):
    written = 0
    while written < len(data):
        n = sink.write(data[written:])
        if n <= 0:
            raise IOError('write made no progress')
        written += n
    return written
