import json
import os
import farmbot  # noqa: F401


def test_package_imports():
    assert farmbot.__doc__


def test_example_config_is_valid_json():
    root = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(root, "farmbot", "config.example.json")) as f:
        cfg = json.load(f)
    assert cfg["device_serial"]
    assert cfg["caps"]["max_actions"] > 0
    assert isinstance(cfg["routine"], list) and cfg["routine"]
