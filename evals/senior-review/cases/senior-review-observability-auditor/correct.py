# Requirement: Every failed background job must emit exactly one job_failed event containing operation_id and error class into events. events.append is the only delivered channel and cannot fail. Job failures are intentionally absorbed to keep processing later jobs.

def run_job(job, operation_id, events):
    try:
        job()
    except Exception as error:
        events.append({'event': 'job_failed', 'operation_id': operation_id, 'class': type(error).__name__})
