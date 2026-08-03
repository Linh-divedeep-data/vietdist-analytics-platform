"""Placeholder import-coverage tests (VDAP-210).

Purpose: make `pytest --collect-only` actually import every module under
src/ and config/, so a broken import fails CI now — not only once real
tests exist. Delete/replace individual functions here as Epic Phase 1
(P1.x tickets) adds real tests for each module.

Imports MUST stay at module level, not inside the test functions: CI's
"Test collection" step runs `pytest --collect-only`, which only imports
this module to discover test functions — it never calls the functions
themselves. An import inside a function body would be silently skipped
by --collect-only and would only break once someone runs the full suite.
"""

import src
from config import settings, sources
from src.extract import ingest_log, lineage, orchestrator, parser, registry
from src.extract.unit_of_work import base


def test_src_package_importable():
    assert src is not None


def test_src_extract_parser_importable():
    assert parser is not None


def test_src_extract_orchestrator_importable():
    assert orchestrator is not None


def test_src_extract_lineage_importable():
    assert lineage is not None


def test_src_extract_registry_importable():
    assert registry is not None


def test_src_extract_ingest_log_importable():
    assert ingest_log is not None


def test_src_extract_unit_of_work_base_importable():
    assert base is not None


def test_config_settings_importable():
    assert settings is not None


def test_config_sources_importable():
    assert sources is not None
