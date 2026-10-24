# Complete private application; public_entry is exported for external consumers.
# The framework calls dispatch and reads REGISTRY, routes named in ROUTES, and __all__.
# No other entry points exist. Dynamic module calls are resolved through globals().
REGISTRY={}
ROUTES={'/hello':'hello'}
def register(name):
    def decorate(fn):
        REGISTRY[name]=fn
        return fn
    return decorate
@register('on_start')
def boot():
    return 'start'
def hello():
    return 'hello'
def public_entry():
    return REGISTRY['on_start']()
__all__=['public_entry']
def retired_migration():
    return 'obsolete'
def dispatch(path):
    return globals()[ROUTES[path]]()

