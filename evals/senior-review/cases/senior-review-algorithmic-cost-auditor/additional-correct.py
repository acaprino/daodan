# export contract: output sink consumes each 1 MiB chunk immediately, peak <=120 MiB.
def export(chunks, sink):
    for chunk in chunks:
        sink.write(chunk)

# Supports finite chains of depth 10000 without consuming recursive stack.
def depth(node):
    count = 0
    while node is not None:
        count += 1
        node = node.next
    return count

# enqueue runs callback off the event loop; submission meets 10ms budget.
def on_event(fetch_sync, enqueue):
    return enqueue(fetch_sync)

# logger.enabled is false for disabled diagnostics.
def trace(items, logger, serialize):
    if logger.enabled:
        for item in items:
            logger.debug(serialize(item))

# Same allocator contract: contiguous availability, not total free memory.
def alloc_or_stream(blocks,request,allocate,stream):
    return allocate(request) if max(blocks,default=0)>=request else stream()

# One parse for the immutable model within this frame.
def render_frame(items,raw,parse,render):
    model=parse(raw)
    for item in items:
        render(item,model)

