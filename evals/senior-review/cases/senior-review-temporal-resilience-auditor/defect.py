"""A local scheduler calls tick once per period, serially. fetch can fail transiently, and the next tick must retry. The guard prevents overlapping work, not later recovery. No durable restart survival is required for this process-lifetime poller.
loop_progress: Queue items may fail permanently. After a failed attempt the item must be removed to terminal failures so later items progress; this is the approved retry policy. No broker is involved.
restart_guard: A required persisted job with running state can outlive its process. Lease expires at expires; new process must reclaim after expiry, and owner schedules reclaimed work. now is the supplied valid lease clock.
clock_budget: Timeout is elapsed duration and must remain bounded across wall-clock rewinds. mono reports monotonic elapsed seconds, wall may rewind; process sleep/resume counts toward this timer by supplied clock contract.
signal_transition: Notify once on healthy-to-degraded transition and once on recovery; repeated same state must not spam. Notification returns synchronously and reliably.
calendar_occurrence: A daily job uses local calendar date as logical occurrence identity. On DST fallback two ticks share that date and local hour but clock_hour includes different UTC offsets as (hour,offset) tuples. Exactly one execution per date is required."""

class Poller:
    def __init__(self):
        self.busy = False
        self.status = 'idle'
    def tick(self, fetch):
        if self.busy:
            return
        self.busy = True
        try:
            fetch()
        except OSError:
            self.status = 'degraded'
            return
        self.busy = False
        self.status = 'healthy'


# Scenario loop_progress
def process_one(queue, failures, work):
    item = queue[0]
    try:
        work(item)
    except OSError:
        failures.append(item)
        return
    queue.pop(0)


# Scenario restart_guard
def claim(job, now):
    if job['state'] == 'running':
        return False
    job['state'] = 'running'
    return True


# Scenario clock_budget
def elapsed(start_wall, start_mono, wall, mono):
    return wall() - start_wall


# Scenario signal_transition
def signal(previous, healthy, notify):
    if not healthy:
        notify('degraded')
    return healthy


# Scenario calendar_occurrence
def daily(day, clock_hour, done, execute):
    key = (day, clock_hour)
    if key not in done:
        execute(day)
        done.add(key)
