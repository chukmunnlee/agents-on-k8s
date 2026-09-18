import contextlib, io, json, traceback, os, base64

REQ, IN, RESP = "/tmp/ks.req", "/tmp/ks.in", "/tmp/ks.resp"
state = {"__name__": "__main__"}

for f in [ REQ, RESP ]:
    if not os.path.exists(f):
        os.mkfifo(f)

while True:
    with open(REQ) as f:
        f.read()
    with open(IN) as f:
        payload = base64.b64decode("".join(f.readlines()))
        code = json.loads(payload)["code"]
        print(f"code: {code}")

    buf, error = io.StringIO(), None
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, state)
    except BaseException as exc:
        if type(exc).__name__ == "FinalAnswerException":
            error = {"name": "FinalAnswerException", "value": exc.value}
        else:
            error = {
                "name": type(exc).__name__,
                "value": str(exc),
                "traceback": traceback.format_exc(),
            }

    with open(RESP, "w") as f:
        print(f'OUTPUT buf: {buf.getvalue()}')
        print(f'OUTPUT error: {error}')
        encoded = base64.b64encode(json.dumps({"logs": buf.getvalue(), "error": error}).encode()).decode()
        f.write(encoded)
        f.flush()
