import os
from typing import Dict


def get_credentials(path: str) -> Dict[str, str]:
    """
    Reads the credentials from the given path
    :param path: Path to the credentials file
    :return:
    """
    assert os.path.exists(path), f"Credentials does not exist at {path}"
    with open(path, "r") as f:
        # Read line by line, replaces the spaces, splits on the first ":"
        # The first part is the key, the second part contains the value in between quotes
        credentials: Dict[str, str] = {}
        for line in f.readlines():
            elt = line.replace(" ", "").replace("\n", "").split(":")
            if len(elt) == 2:
                credentials[elt[0]] = elt[1]
        return credentials
