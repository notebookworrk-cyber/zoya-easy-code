"""Test the Zoya 4.0 web framework."""

import sys
sys.path.insert(0, r"C:\Users\hp\zoya3")

try:
    from zoya.web import Web, create_app, create_success, create_error
    from zoya.web.response import ResponseData, HTTP_200_OK, HTTP_400_BAD_REQUEST
    from zoya.web.router import Router, Route
    from zoya.web.middleware import (
        BaseMiddleware,
        LoggingMiddleware,
        AuthMiddleware,
        ErrorHandlingMiddleware,
    )

    print("[OK] All imports succeeded")

    # Test Router
    router = Router()

    def handle_home(request):
        return "Hello from /"

    router.route("GET", "/", handle_home)
    handler = router.handle("GET", "/", None)
    result = handler(None)
    assert result == "Hello from /"
    print("[OK] Router basic test passed")

    # Test Path parameters via decorator
    @router.route("GET", "/users/{id}")
    def handle_user(request, id):
        return f"User {id}"

    handler = router.handle("GET", "/users/42", None)
    result = handler(None, id="42")
    assert result == "User 42"
    print("[OK] Router parameter test passed")

    # Test Router.match raises KeyError
    try:
        router.match("GET", "/nope")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass
    print("[OK] Router.match raises KeyError on no match")

    # Test ResponseData create_success/create_error
    success = create_success({"name": "Zoya"}, meta={"page": 1})
    assert success["success"] is True
    assert success["data"] == {"name": "Zoya"}
    assert success["error"] is None
    assert success["meta"] == {"page": 1}
    print("[OK] create_success test passed")

    error = create_error("Bad request", status=HTTP_400_BAD_REQUEST, meta={"field": "id"})
    assert error["success"] is False
    assert error["data"] is None
    assert error["error"] == "Bad request"
    print("[OK] create_error test passed")

    # Test middleware classes are instantiable
    lm = LoggingMiddleware()
    auth = AuthMiddleware(lambda req: True)
    eh = ErrorHandlingMiddleware()
    assert isinstance(lm, BaseMiddleware)
    assert isinstance(auth, BaseMiddleware)
    assert isinstance(eh, BaseMiddleware)
    print("[OK] Middleware classes instantiate")

    # Test Web app factory
    app = create_app()
    assert isinstance(app, Web)
    print("[OK] create_app returns a Web instance")

    print("\n*** ALL WEB TESTS PASSED ***")
except Exception as exc:
    print(f"[FAIL] {type(exc).__name__}: {exc}")
    raise
