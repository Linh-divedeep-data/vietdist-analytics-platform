# config/settings.py
"""Đường dẫn các lớp Data Lake — cố định theo kiến trúc Medallion (CLAUDE.md).

Không đặt FOLDER_ID/SERVICE_ACCOUNT_FILE ở đây: gdrive_connector.py cần đọc
os.getenv() trực tiếp tại thời điểm import của chính nó để 1 số test dùng
importlib.reload(gdrive_connector) re-eval được biến môi trường mới — gián
tiếp qua module khác sẽ bị cache giá trị cũ, phá test đó.
"""

RAW_DIR = "data/raw"
BRONZE_DIR = "data/bronze"
SILVER_DIR = "data/silver"
GOLD_DIR = "data/gold"
