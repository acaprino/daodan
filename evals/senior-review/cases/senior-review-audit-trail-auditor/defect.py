"""Every privileged update must create exactly one attributable audit record for its real actor and target. The sink is append-only but one physical line is interpreted as one record; actor display names may contain newlines. Transport integrity and access control are supplied.
alternate_action: Both single and batch changes require an attributable immutable event. audit_write has authoritative actor and append-only delivery; its failure prevents the change. apply_change is otherwise authorized."""

def audit(sink, actor_id, display_name, target):
    sink.append(f'{actor_id}|{display_name}|update|{target}\n')


# Scenario alternate_action
def sensitive_change(actor, target, audit_write, apply_change):
    audit_write(actor, target)
    return apply_change(target)
def sensitive_batch(actor, targets, audit_write, apply_change):
    return [apply_change(target) for target in targets]
