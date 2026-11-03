"""Cap request bodies before multipart parsing, including chunked uploads."""
from tempfile import SpooledTemporaryFile

import anyio
from starlette.responses import JSONResponse

MAX_REQUEST_BYTES = 42 * 1024 * 1024  # Existing 40 MiB filing limit plus multipart overhead.


class RequestLimitMiddleware:
    def __init__(self, app, max_bytes=MAX_REQUEST_BYTES, timeout_seconds=30):
        self.app, self.max_bytes, self.timeout_seconds = app, max_bytes, timeout_seconds

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def reject(status, message):
            await JSONResponse({"data": None, "meta": {"status": "error", "is_mock": False,
                "is_stale": False, "warnings": [message]},
                "errors": [{"code": "REQUEST_LIMIT", "message": message}], "detail": message},
                status_code=status, headers={"Cache-Control": "private, no-store"})(scope, receive, send)

        headers = dict(scope["headers"])
        declared = headers.get(b"content-length")
        if declared is not None and (not declared.isdigit() or len(declared) > 12 or int(declared) > self.max_bytes):
            return await reject(413, "Request body exceeds the 42 MiB limit.")
        with SpooledTemporaryFile(max_size=1024 * 1024) as body:
            length = 0
            try:
                with anyio.fail_after(self.timeout_seconds):
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            return
                        chunk = message.get("body", b"")
                        length += len(chunk)
                        if length > self.max_bytes:
                            return await reject(413, "Request body exceeds the 42 MiB limit.")
                        body.write(chunk)
                        if not message.get("more_body", False):
                            break
            except TimeoutError:
                return await reject(408, "Request body timed out. Try the upload again.")
            body.seek(0)
            delivered = 0
            finished = False

            async def replay():
                nonlocal delivered, finished
                if finished:
                    return await receive()
                chunk = body.read(64 * 1024)
                delivered += len(chunk)
                finished = delivered >= length
                return {"type": "http.request", "body": chunk, "more_body": not finished}

            await self.app(scope, replay, send)
