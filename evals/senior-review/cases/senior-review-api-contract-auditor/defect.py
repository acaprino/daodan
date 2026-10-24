"""The authoritative response contract is id:string. Producer and consumer ship atomically from one codebase, but the serialized payload still must match this contract. Mock and actual serializer are shown. Consumers use string methods. A separate OpenAPI document is not required.
request_and_error: The interface accepts integer limit1..10 and rejects missing/NULL/string/unknown fields with JSON {error:invalid}, status400. Accepted response is JSON with items and status200; client always decodes JSON.
strict_compatibility: Old consumer remains supported and accepts only status=ready or busy plus id:string. It rejects unknown fields. New producer is not atomically deployed with that consumer; changing the schema document alone does not remove support.
protobuf_tags: Wire tag1 is immutable string account_id for supported old readers. New region field must not reuse tag1; encoder returns numeric-tag payload and old_reader interprets tag1 as account identity.
graphql_nullability: GraphQL schema declares display:String! for each returned user. Stored display may be NULL; the approved resolver fallback is user ID. A selected display field must not bubble null into the parent response.
stream_terminal: AI provider chunks may be partial; only complete output with finish=stop may reach consume, and it must contain id:string. Refusal/truncation must return failed. Schema examples never authorize actions.
units_and_cursor: The external API requires timeout seconds while caller budget is integer milliseconds. Pagination cursor on the wire must be a string even when internal ID is numeric.
retained_message: Retained wire version1 uses event_id and value; current version2 uses event_id and payload. Both are supported. Unknown versions and malformed values must fail explicitly; JSON scalar value must be a string."""

import json
from typing import TypedDict
class Response(TypedDict):
    id: str
def mock() -> Response:
    return {'id': '7'}
def serialize(row):
    return json.dumps({'id': row['id']})
def consume(payload):
    return json.loads(payload)['id'].lower()


# Scenario request_and_error
def request_response(body):
    import json
    try:
        limit = int(body.get('limit', 10))
        return 200, json.dumps({'items': list(range(limit))})
    except (TypeError, ValueError):
        return 400, '<html>invalid</html>'


# Scenario strict_compatibility
def supported_payload():
    return {'id': '7', 'status': 'paused', 'new_optional': 1}


# Scenario protobuf_tags
def encoded_message(account_id, region):
    return {1: region, 2: account_id}
def old_reader(wire):
    return wire[1]


# Scenario graphql_nullability
def display_resolver(user):
    return user['display']


# Scenario stream_terminal
def ai_result(chunks, finish, consume):
    import json
    value = json.loads(''.join(chunks))
    return consume(value)


# Scenario units_and_cursor
def request_args(budget_ms, row_id):
    return {'timeout_seconds': budget_ms, 'cursor': row_id}


# Scenario retained_message
def decode_message(message):
    return message['payload']
