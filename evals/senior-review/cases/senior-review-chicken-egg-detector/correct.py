"""Cold start begins with schema_ready=False. Serving requires the schema; the only schema creator is migrate. start returns whether useful service becomes ready. There is no external migrator in this deployment. Existing upgraded stores may already be ready.
early_default: First construction may occur before required endpoint configuration arrives. A later configure call must bind the endpoint before readiness; initialized means the endpoint is usable.
readiness_order: Traffic can arrive immediately when router.publish is called. Requests require migrated schema and initialized pool. Migration is independent and supports the prior schema; no first request may see an uninitialized dependency."""

def serve(state):
    return state['schema_ready']
def migrate(state):
    state['schema_ready'] = True
def start(state):
    migrate(state)
    return serve(state)


# Scenario early_default
class Service:
    def __init__(self):
        self.endpoint = None
        self.initialized = False
    def configure(self, endpoint):
        if not self.initialized:
            self.endpoint = endpoint
            self.initialized = True


# Scenario readiness_order
def boot(router, migrate, init_pool):
    migrate()
    init_pool()
    router.publish()
