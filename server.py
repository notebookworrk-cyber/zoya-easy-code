import uvicorn
from zoya.web import Web, Request
from zoya.web.response import create_success

app = Web()


@app.router.route("GET", "/")
def home(req):
    return {"message": "Hello from Zoya!"}


@app.router.route("GET", "/hello/{name}")
def greet(req):
    name = req.scope["path"].split("/")[-1]
    return {"greeting": f"Hey {name}!"}


async def asgi_app(scope, receive, send):
    if scope["type"] != "http":
        return
    request = Request(scope, receive)
    handler = app.router.handle(request.method, request.path, request)
    result = handler(request) if callable(handler) else handler
    if isinstance(result, dict):
        body = str(result).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [("content-type", "application/json")],
            }
        )
        await send({"type": "http.response.body", "body": body})


uvicorn.run(asgi_app, host="127.0.0.1", port=8080)
