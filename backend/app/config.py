import os

USE_DOCKER = os.getenv(
    "USE_DOCKER",
    "false"
).lower() == "true"