import os

from src.extract.orchestrator import get_bronze_output_dir


def test_get_bronze_output_dir_strips_dashes_from_run_date(tmp_path):
    out_dir = get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))

    assert out_dir == os.path.join(str(tmp_path), "20260722")


def test_get_bronze_output_dir_creates_directory_on_disk(tmp_path):
    out_dir = get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))

    assert os.path.isdir(out_dir)


def test_get_bronze_output_dir_returns_same_path_on_repeated_calls(tmp_path):
    first = get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))
    second = get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))

    assert first == second


def test_get_bronze_output_dir_does_not_raise_when_directory_already_exists(tmp_path):
    get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))

    # must not raise on the second call even though the directory already exists
    get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))
