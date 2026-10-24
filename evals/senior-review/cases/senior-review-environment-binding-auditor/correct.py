# Requirement: staging must read only stage-db; production must read only prod-db. Deployment invokes config with ENV=staging or ENV=production. The returned database is the sole runtime binding; no later overrides exist.

DATABASES = {'staging': 'stage-db', 'production': 'prod-db'}
def config(env):
    return {'database': DATABASES[env['ENV']]}
