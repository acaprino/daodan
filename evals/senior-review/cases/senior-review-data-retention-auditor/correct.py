"""Approved policy: a deletion request removes a customer from primary and search immediately. Backups may retain encrypted copies for 30 days, but every restore must apply the durable deletion set before serving reads. deleted is retained separately from backups.
copy_completion: Primary and search copies must both be deleted unless legal_hold is true. Provider deletion may fail; on failure caller must receive failure and retain work for retry. The caller below owns the pending map for the process lifetime and removes a key only after the helper returns complete; no crash/restart survival is required in this scene. The helper borrows the key and cannot consume pending work. Provider deletion is idempotent; normal return means the copy is deleted and OSError means it remains."""

def erase(customer_id, primary, search, deleted):
    deleted.add(customer_id)
    primary.pop(customer_id, None)
    search.pop(customer_id, None)
def restore(backup, deleted):
    return {key: value for key, value in backup.items() if key not in deleted}


# Scenario copy_completion
def delete_copies(key, legal_hold, primary, search):
    if legal_hold:
        return 'held'
    primary.delete(key)
    search.delete(key)
    return 'complete'

def run_pending(pending, key, primary, search):
    if key not in pending:
        return 'absent'
    try:
        result = delete_copies(key, pending[key]['legal_hold'], primary, search)
    except OSError:
        return 'retry'
    if result == 'complete':
        del pending[key]
    return result
