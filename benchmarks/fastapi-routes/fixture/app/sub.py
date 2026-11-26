from fastapi import FastAPI

sub = FastAPI()
tenant = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)  # no documentation routes
embedded = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)  # mounted on a router that the application includes


@sub.get("/hello")
def hello():
    return {"hello": True}


@sub.get("/items/{item_id}")
async def sub_item(item_id: int):
    return {"item": item_id}


@tenant.get("/info")
def tenant_info():
    return {"tenant": True}


@embedded.get("/leaf")
def embedded_leaf():
    return {"leaf": True}
