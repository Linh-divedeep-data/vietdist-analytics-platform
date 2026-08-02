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
    """
    TODO: HỌC VIÊN TỰ VIẾT CODE CHO HÀM NÀY
    
    Yêu cầu:
    1. Kiểm tra xem thư mục `destination_folder` đã tồn tại chưa, nếu chưa thì tạo mới (dùng os.makedirs).
    2. Gọi Google Drive API (sử dụng đối tượng `drive_service` ở trên) để lấy luồng dữ liệu của file (get_media).
    3. Dùng thư viện `io.FileIO` và `MediaIoBaseDownload` để tải từng chunk dữ liệu về và lưu thành file vật lý trên máy tính.
    4. Trả về đường dẫn tuyệt đối hoặc tương đối của file vừa tải.
    
    Gợi ý: Tìm kiếm từ khóa "Google Drive API python download file get_media" trên Google.
    """
    pass

if __name__ == "__main__":
    # Đây là FOLDER_ID chứa dữ liệu gốc của dự án VietDist
    FOLDER_ID = "1or8Z1cuL8pkcRypbv3odkMbhAgpje_lr"
    
    print("Dang lay danh sach file...")
    files = list_files_in_folder(FOLDER_ID)
    
    if not files:
        print("Khong tim thay file nao.")
    else:
        print(f"Tim thay {len(files)} files. Hay hoan thanh ham download_file() de tai file nhe!")