import promptfw


def test_module_name():
    assert promptfw.__name__ == "promptfw"


def test_version_is_str():
    assert isinstance(promptfw.__version__, str)
