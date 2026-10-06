from app.config import _list_env


def test_list_env_defaults_to_empty(monkeypatch):
    monkeypatch.delenv("SOME_UNSET_LIST_VAR", raising=False)
    assert _list_env("SOME_UNSET_LIST_VAR") == []


def test_list_env_parses_comma_separated_values(monkeypatch):
    monkeypatch.setenv(
        "SOME_LIST_VAR",
        "chrome-extension://abcdefghijklmnopabcdefghijklmnop, moz-extension://11111111-1111-1111-1111-111111111111",
    )
    assert _list_env("SOME_LIST_VAR") == [
        "chrome-extension://abcdefghijklmnopabcdefghijklmnop",
        "moz-extension://11111111-1111-1111-1111-111111111111",
    ]


def test_list_env_ignores_blank_entries(monkeypatch):
    monkeypatch.setenv("SOME_LIST_VAR", "one,, two ,")
    assert _list_env("SOME_LIST_VAR") == ["one", "two"]
