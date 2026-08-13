from pathlib import Path

from config import settings


def test_raw_dir_is_data_raw():
    assert Path(settings.RAW_DIR) == settings.ROOT_DIR / "data" / "raw"


def test_bronze_dir_is_data_bronze():
    assert Path(settings.BRONZE_DIR) == settings.ROOT_DIR / "data" / "bronze"


def test_silver_dir_is_data_silver():
    assert Path(settings.SILVER_DIR) == settings.ROOT_DIR / "data" / "silver"


def test_gold_dir_is_data_gold():
    assert Path(settings.GOLD_DIR) == settings.ROOT_DIR / "data" / "gold"


def test_dirs_are_absolute_paths():
    assert Path(settings.RAW_DIR).is_absolute()
    assert Path(settings.BRONZE_DIR).is_absolute()
    assert Path(settings.SILVER_DIR).is_absolute()
    assert Path(settings.GOLD_DIR).is_absolute()


def test_settings_module_has_no_credential_fields():
    assert not hasattr(settings, "FOLDER_ID")
    assert not hasattr(settings, "SERVICE_ACCOUNT_FILE")
