# Independent contracts: export chunks total 100 MiB; peak retained payload <= 120 MiB.
# chunks is an iterator of 1 MiB bytes; consuming it has no other allocations.
def export(chunks):
    parts = list(chunks)
    return b''.join(parts)

# Supported chain depth is 10000; runtime recursion limit is 1000.
# Node is a single next pointer ending in None.
def depth(node):
    return 0 if node is None else 1 + depth(node.next)

# event_loop invokes this for each event; fetch_sync blocks 2 seconds.
# Required event-loop uninterrupted work <= 10ms. enqueue runs callback off-loop.
def on_event(fetch_sync, enqueue):
    return fetch_sync()

# Disabled logger never uses payload. serialize allocates 10 MiB and runs per item.
# Requirement: disabled diagnostics perform no serialization.
def trace(items, logger, serialize):
    for item in items:
        logger.debug(serialize(item))

# Allocator inventory: free blocks [8,8] MiB; request is 12 MiB contiguous.
# Contract: fall back to streaming whenever no single block suffices.
def alloc_or_stream(blocks,request,allocate,stream):
    return allocate(request) if sum(blocks)>=request else stream()

# Non-React renderer calls this per item; full immutable model has 10000 items.
# Contract: at most one parse per frame for all rows.
def render_frame(items,raw,parse,render):
    for item in items:
        render(item,parse(raw))

