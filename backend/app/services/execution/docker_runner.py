import docker
import tempfile
import os
import shutil

class DockerRunner:

    def __init__(
        self,
        image_name: str = "nexus-sandbox-python:latest"
    ):
        self.client = docker.from_env()
        self.image = image_name

    def execute(
        self,
        code: str,
        stdin_input: str = ""
    ) -> str:

        temp_dir = tempfile.mkdtemp()

        code_path = os.path.join(
            temp_dir,
            "code.py"
        )

        with open(
            code_path,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(code)

        container = None

        try:

            container = self.client.containers.run(
                image=self.image,
                command="python /sandbox/code.py",
                volumes={
                    temp_dir: {
                        "bind": "/sandbox",
                        "mode": "ro"
                    }
                },
                working_dir="/sandbox",
                mem_limit="256m",
                nano_cpus=int(0.5 * 1e9),
                network_disabled=True,
                detach=True,
                remove=False
            )

            try:
                container.wait(timeout=5)

            except Exception:
                return "TIMEOUT_ERROR"

            logs = container.logs(
                stdout=True,
                stderr=True
            ).decode()

            logs = logs.strip()

            if not logs:
                return "NO_OUTPUT"

            if (
                "Module os blocked" in logs
                or "Module subprocess blocked" in logs
                or "Module socket blocked" in logs
                or "Module shutil blocked" in logs
            ):
                return "SECURITY_ERROR"

            if "MemoryError" in logs:
                return "MEMORY_ERROR"

            return logs

        except docker.errors.APIError:
            return "SECURITY_ERROR"

        except Exception as e:

            error_message = str(e)

            if "timed out" in error_message.lower():
                return "TIMEOUT_ERROR"

            if "memory" in error_message.lower():
                return "MEMORY_ERROR"

            return (
                f"EXECUTION_ERROR: "
                f"{error_message}"
            )

        finally:

            if container:

                try:
                    container.remove(force=True)
                except:
                    pass

            try:
                shutil.rmtree(temp_dir)
            except:
                pass


            