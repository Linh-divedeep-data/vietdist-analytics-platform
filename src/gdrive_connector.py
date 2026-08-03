"""Google Drive connector (VDAP-173): Service Account auth + list files in a folder.

get_drive_service() builds a fresh client per call (no module-level
caching) so this module can be imported in tests without live
credentials — tests monkeypatch get_drive_service() itself.
"""

import os

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials.json")


def get_drive_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(
            f"Không tìm thấy file {SERVICE_ACCOUNT_FILE}. Đặt file ở thư mục gốc dự án "
            "hoặc set GOOGLE_SERVICE_ACCOUNT_JSON trong .env."
        )
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("drive", "v3", credentials=credentials)


def list_files_in_folder(folder_id: str) -> list[dict]:
    service = get_drive_service()
    query = f"'{folder_id}' in parents and trashed=false"

    files: list[dict] = []
    page_token = None
    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
        ).execute()
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return files


def get_folder_id_from_env() -> str:
    folder_id = os.getenv("GDRIVE_FOLDER_ID")
    if not folder_id:
        raise RuntimeError(
            "GDRIVE_FOLDER_ID chưa được set trong .env — không biết đọc folder Drive nào."
        )
    return folder_id


if __name__ == "__main__":
    folder_id = get_folder_id_from_env()
    print("Đang lấy danh sách file...")
    files = list_files_in_folder(folder_id)
    print(f"Tìm thấy {len(files)} file(s).")
    for f in files:
        print(f"  {f['name']} ({f['mimeType']})")
