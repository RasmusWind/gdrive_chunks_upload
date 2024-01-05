import shutil
import sys
from gdrive import gdrive_authentication, upload
from chunk_compression import compress_path

def compress_and_upload(path_to_compress: str, gdrive_access_token_path: str, gdrive_base_id: str, gdrive_folder_id: str, delete_after_upload=False) -> None:
    drive = gdrive_authentication(gdrive_access_token_path)
    new_path = compress_path(path_to_compress)

    if new_path and drive:
        upload(drive, gdrive_base_id, gdrive_folder_id, new_path)
        if delete_after_upload:
            shutil.rmtree(new_path)
    else:
        print(f"Error. {'Problem with drive. ' if not drive else ''}{'Problem with compressed file path. ' if not new_path else ''}")
    
if __name__ == "__main__":
    try:
        ptc = sys.argv[1]
        gatp = sys.argv[2]
        gbi = sys.argv[3]
        gfi = sys.argv[4]
        dau = True if sys.argv[5] == "True" else False
        compress_and_upload(ptc, gatp, gbi, gfi, dau)
    except Exception:
        print("Error passing arguments.")