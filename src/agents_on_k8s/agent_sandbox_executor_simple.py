from __future__ import annotations

import base64, json, os

from k8s_agent_sandbox.sandbox_client import SandboxClient
from k8s_agent_sandbox.models import SandboxInClusterConnectionConfig
from smolagents.local_python_executor import CodeOutput
from smolagents.monitoring import LogLevel
from smolagents.remote_executors import RemotePythonExecutor
from smolagents.utils import AgentError

REQ, IN, RESP = "/tmp/ks.req", "/tmp/ks.in", "/tmp/ks.resp"

KERNEL_SOURCE = r'''
import contextlib, io, json, traceback

REQ, IN, RESP = "/tmp/ks.req", "/tmp/ks.in", "/tmp/ks.resp"
state = {"__name__": "__main__"}

while True:
    with open(REQ) as f:
        f.read()
    with open(IN) as f:
        code = json.load(f)["code"]

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
        f.write(json.dumps({"logs": buf.getvalue(), "error": error}))
'''


class AgentSandboxExecutor(RemotePythonExecutor):
    def __init__(
        self,
        additional_imports: list[str],
        logger,
        allow_pickle: bool = False,
        warmpool: str = "python-sandbox-warmpool",
        namespace: str = "default",
        connection_config=None,):

        super().__init__(additional_imports, logger, allow_pickle)

        #encoded = base64.b64encode(KERNEL_SOURCE.encode()).decode()
        #self.sandbox.commands.run(
        #    f"mkfifo -m 600 {REQ} {RESP} 2>/dev/null; "
        #    f"printf %s {encoded} | base64 -d > /tmp/kernel.py"
        #)
        for f in [ REQ, RESP ]:
            if not os.path.exists(f):
                os.mkfifo(f)

        with open("/tmp/kernel.py", "w") as f:
            f.write(KERNEL_SOURCE)
            f.flush()

        self.client = SandboxClient(
            connection_config=connection_config or SandboxInClusterConnectionConfig()
        )
        self.sandbox = self.client.create_sandbox(warmpool=warmpool, namespace=namespace)

        self.sandbox.commands.run("nohup python3 -u /tmp/kernel.py > /tmp/kernel.log 2>&1 &")

        self.installed_packages = self.install_packages(
            list({"smolagents", *additional_imports})
        )

    def install_packages(self, additional_imports: list[str]) -> list[str]:
        if additional_imports:
            self.sandbox.commands.run("pip install --quiet " + " ".join(additional_imports))
        return additional_imports

    def run_code_raise_errors(self, code: str) -> CodeOutput:
        encoded = base64.b64encode(json.dumps({"code": code}).encode()).decode()
        result = self.sandbox.commands.run(
            f"printf %s {encoded} | base64 -d > {IN} && echo go > {REQ} && cat {RESP}"
        )

        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise AgentError(f"Sandbox returned:\n{result.stdout}", self.logger)

        error = response.get("error")
        if error is None:
            return CodeOutput(output=None, logs=response["logs"], is_final_answer=False)

        if error["name"] == self.FINAL_ANSWER_EXCEPTION:
            return CodeOutput(
                output=self._deserialize_final_answer(error["value"], self.allow_pickle),
                logs=response["logs"],
                is_final_answer=True,
            )

        raise AgentError(
            f"{response['logs']}\n{error['name']}: {error['value']}\n"
            f"{error.get('traceback', '')}",
            self.logger,
        )

    def cleanup(self) -> None:
        if getattr(self, "sandbox", None) is not None:
            self.sandbox.terminate()
            self.sandbox = None

    def delete(self) -> None:
        self.cleanup()
