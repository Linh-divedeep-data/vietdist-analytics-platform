from config import settings


def test_raw_dir_is_data_raw():
    assert settings.RAW_DIR == "data/raw"


def test_bronze_dir_is_data_bronze():
    assert settings.BRONZE_DIR == "data/bronze"


def test_silver_dir_is_data_silver():
    assert settings.SILVER_DIR == "data/silver"


def test_gold_dir_is_data_gold():
    assert settings.GOLD_DIR == "data/gold"


def test_settings_module_has_no_credential_fields():
    assert not hasattr(settings, "FOLDER_ID")
    assert not hasattr(settings, "SERVICE_ACCOUNT_FILE")
