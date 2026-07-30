import io
import os

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

load_dotenv()

# Cấu hình Scopes yêu cầu quyền đọc Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Lấy đường dẫn file credentials từ biến môi trường (trong file .env)
# Ví dụ trong .env: GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials.json")

# FOLDER_ID chứa dữ liệu gốc của dự án VietDist — lấy từ .env, không hardcode
# (khác môi trường dev/prod cần trỏ tới folder khác nhau)
# Ví dụ trong .env: GDRIVE_FOLDER_ID=your_google_drive_folder_id_here
FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")

def get_drive_service():
    """Khởi tạo và trả về đối tượng service để gọi Google Drive API."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Không tìm thấy file {SERVICE_ACCOUNT_FILE}. Hãy đảm bảo bạn đã đặt file ở thư mục gốc của dự án.")
    
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    
    drive_service = build(
        "drive",
        "v3",
        credentials=credentials
    )
    return drive_service

drive_service = get_drive_service()

def list_files_in_folder(folder_id):
    """Lấy danh sách các file trong một thư mục cụ thể trên Google Drive."""
    query = f"'{folder_id}' in parents and trashed=false"
    results = drive_service.files().list(
        q=query, 
        fields="files(id, name, mimeType)"
    ).execute()
    
    return results.get("files", [])

def download_file(file_id, file_name, destination_folder="data/raw"):
    """Tải 1 file từ Google Drive về destination_folder, trả về đường dẫn file đã tải."""
    os.makedirs(destination_folder, exist_ok=True)
    file_path = os.path.join(destination_folder, file_name)

    request = drive_service.files().get_media(fileId=file_id)
    try:
        with io.FileIO(file_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

    return file_path

if __name__ == "__main__":
    if not FOLDER_ID:
        raise RuntimeError("GDRIVE_FOLDER_ID chưa được set trong .env")

    print("Dang lay danh sach file...")
    files = list_files_in_folder(FOLDER_ID)
    
    if not files:
        print("Khong tim thay file nao.")
    else:
        print(f"Tim thay {len(files)} files. Hay hoan thanh ham download_file() de tai file nhe!")
