"""Google Drive connector (VDAP-173): Service Account auth + list files in a folder.

get_drive_service() builds a fresh client per call (no module-level
caching) so this module can be imported in tests without live
credentials — tests monkeypatch get_drive_service() itself.
"""

import io
import os
import time

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from config.constants import GDRIVE_BACKOFF_SECONDS, GDRIVE_MAX_ATTEMPTS

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


_MAX_ATTEMPTS = GDRIVE_MAX_ATTEMPTS
_RETRYABLE_STATUS_CODES = {429, 500, 503}
_BACKOFF_SECONDS = GDRIVE_BACKOFF_SECONDS
_sleep = time.sleep


def _download_attempt(file_id: str, destination_path: str) -> None:
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(destination_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def _cleanup_partial_file(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def download_file(file_id: str, file_name: str, destination_folder: str = "data/raw") -> str:
    os.makedirs(destination_folder, exist_ok=True)
    destination_path = os.path.join(destination_folder, file_name)

    for attempt in range(_MAX_ATTEMPTS):
        try:
            _download_attempt(file_id, destination_path)
            return destination_path
        except HttpError as error:
            _cleanup_partial_file(destination_path)
            is_last_attempt = attempt == _MAX_ATTEMPTS - 1
            if error.resp.status not in _RETRYABLE_STATUS_CODES or is_last_attempt:
                raise
            _sleep(_BACKOFF_SECONDS[attempt])
        except TimeoutError:
            _cleanup_partial_file(destination_path)
            if attempt == _MAX_ATTEMPTS - 1:
                raise
            _sleep(_BACKOFF_SECONDS[attempt])


if __name__ == "__main__":
    folder_id = get_folder_id_from_env()
    print("Đang lấy danh sách file...")
    files = list_files_in_folder(folder_id)
    print(f"Tìm thấy {len(files)} file(s).")
    for f in files:
        print(f"  {f['name']} ({f['mimeType']})")
