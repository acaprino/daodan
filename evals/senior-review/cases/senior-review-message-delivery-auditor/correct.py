"""The AMQP adapter removes a message permanently on ack; unacked messages redeliver after disconnect. process durably applies an event with logical-ID deduplication or raises before commit. No message may be lost on crash before commit.
publish_routing: A successful publish means routed to the required durable queue. transport returns {confirmed,routed}; confirmation alone can acknowledge an unroutable publish. Unroutable or unconfirmed publication must remain pending.
ack_range: Delivery tags1 and2 are in flight on one channel. Work2 can finish before work1. ack(tag,multiple=True) confirms every tag through tag; incomplete work must not be acknowledged.
ordering_identity: Entity events carry monotonic sequence; wall clocks across nodes can differ. apply_ordered is serial and must not regress sequence.
logical_redelivery: Republish preserves logical_id and payload but changes transport_id. Deliveries are serial and apply_event returns normally; each callback call emits one observable application. Each logical event must cause exactly one application across its deliveries, regardless of transport identity. This scene is independent of timestamp ordering.
terminal_routing: After3failed attempts a poison message must leave the work queue and remain available to operator redrive. message['attempts'] is the application attempt number that just failed, starting at1. republish preserves the supplied application field; its separate broker delivery counter resets to0. archive is durable retained terminal storage, so no DLQ product is required.
partition_commit: Kafka-style commit(offset) acknowledges all prior offsets in the partition. Offsets10and11 process concurrently; only11has finished. Commit must not cover unfinished10."""

def handle(channel, message, process):
    process(message['event'])
    channel.ack(message['delivery_tag'])


# Scenario publish_routing
def publish_result(transport, event):
    result = transport(event)
    return 'done' if result['confirmed'] and result['routed'] else 'pending'


# Scenario ack_range
def finish_second(channel):
    channel.ack(2, multiple=False)


# Scenario ordering_identity
def apply_ordered(state, event):
    if event['sequence'] > state['sequence']:
        state['value'] = event['value']
        state['sequence'] = event['sequence']

# Scenario logical_redelivery
def apply_once(seen, event, apply_event):
    key = event['logical_id']
    if key in seen:
        return
    apply_event(event)
    seen.add(key)

# Scenario terminal_routing
def failed_message(message, republish, archive):
    if message['attempts'] >= 3:
        archive(message)
    else:
        republish(dict(message, attempts=message['attempts'] + 1))


# Scenario partition_commit
def finish_offset(commit, finished):
    next_offset = 10
    while next_offset in finished:
        next_offset += 1
    if next_offset > 10:
        commit(next_offset)
