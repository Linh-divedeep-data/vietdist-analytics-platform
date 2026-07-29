import uuid

from main import main


def test_main_returns_valid_uuid_batch_id():
    batch_id = main()
    assert uuid.UUID(batch_id)


def test_main_generates_new_batch_id_each_call():
    first = main()
    second = main()
    assert first != second


def test_main_logs_carry_the_same_batch_id(capsys):
    batch_id = main()
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) >= 2
    for line in lines:
        assert f"[batch_id={batch_id}]" in line
