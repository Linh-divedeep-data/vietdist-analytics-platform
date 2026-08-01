from config.sources import CSV_SOURCES, EXCEL_SOURCES
from src.extract.registry import UNIT_OF_WORK


def test_registry_has_exactly_10_sources():
    assert len(UNIT_OF_WORK) == 10


def test_registry_keys_match_config_sources_exactly():
    assert set(UNIT_OF_WORK.keys()) == set(CSV_SOURCES) | set(EXCEL_SOURCES)


def test_registry_values_are_callable():
    assert all(callable(run_fn) for run_fn in UNIT_OF_WORK.values())
