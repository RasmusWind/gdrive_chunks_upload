import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive, GoogleDriveFile, GoogleDriveFileList
from progressbar import ProgressBar
from datetime import datetime

GDRIVE_FOLDER_MIMETYPE = "application/vnd.google-apps.folder"

def TODAY_DAY(date:datetime=None) -> str:
    if not date:
        date = datetime.now()
    return date.strftime('%A')


def FOLDER_SUFFIX() -> str:
    now_date = datetime.now()
    return f"-{TODAY_DAY(now_date)}_{now_date.date()}"


def upload(drive: GoogleDrive, gdrive_base_id: str, gdrive_folder_id: str, path_to_dir: str) -> None:
    cpt = sum([len(files) for r, d, files in os.walk(path_to_dir)])
    pb = ProgressBar("GDRIVE UPLOAD", 0, cpt, True)
    upload_dir_to_gdrive(drive, gdrive_base_id, gdrive_folder_id, path_to_dir, pb)


def gdrive_authentication(access_token_path: str) -> GoogleDrive|None:
    gauth = GoogleAuth()
    try:
        gauth.LoadCredentialsFile(access_token_path)
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
    except Exception:
        print("Google authentication failed. Check credentials.")
        return None
    drive = GoogleDrive(gauth)
    gauth.SaveCredentialsFile(access_token_path)

    return drive


def upload_dir_to_gdrive(drive: GoogleDrive, gdrive_base_id: str, gdrive_folder_id: str, path_to_dir: str, pb:ProgressBar=None) -> None:
    dir_name = os.path.split(path_to_dir)[-1]

    folder = gdrive_folder_exists(drive, gdrive_folder_id, dir_name)
    if folder:
        folder.Delete()

    folder = drive.CreateFile(
        {
            'title': f"{dir_name}{FOLDER_SUFFIX()}",
            'parents': [{
                'kind': 'drive#fileLink',
                'teamDriveId': gdrive_base_id,
                'id': gdrive_folder_id
            }],
            'mimeType': GDRIVE_FOLDER_MIMETYPE
        }
    )
    folder.Upload()

    for d in dir_list(path_to_dir):
        if os.path.isdir(f"{path_to_dir}/{d}"):
            upload_dir_to_gdrive(drive, gdrive_base_id, folder["id"], f"{path_to_dir}/{d}", pb=pb)
        else:
            upload_file_to_gdrive(drive, gdrive_base_id, folder["id"], f"{path_to_dir}/{d}")
            if pb:
                pb.increment_progress()


def upload_file_to_gdrive(drive: GoogleDrive, gdrive_base_id: str, gdrive_folder_id: str, path_to_file: str):
    title = os.path.split(path_to_file)[-1]
    existing_file = gdrive_folder_exists(drive, gdrive_folder_id, os.path.split(path_to_file)[-1])
    if existing_file:
        existing_file.Delete()
    file = drive.CreateFile({
        "title": f"{title}{FOLDER_SUFFIX()}",
        "parents": [{
            'kind': 'drive#fileLink',
            'teamDriveId': gdrive_base_id,
            'id': gdrive_folder_id
        }]
    })
    file.SetContentFile(path_to_file)
    file.Upload()


def dir_list(path):
    dir_elements = os.listdir(path)
    return dir_elements


def gdrive_isdir(gdrivefile:GoogleDriveFile) -> bool:
    return gdrivefile["mimetype"] == GDRIVE_FOLDER_MIMETYPE


def gdrive_dir_list(drive: GoogleDrive, gdrive_base_id: str, gdrive_folder_id: str) -> GoogleDriveFileList:
    element_list = drive.ListFile(
        {
            'q': f"'{gdrive_folder_id}' in parents and trashed=false",
            'supportsAllDrives': True,  # Modified
            'driveId': gdrive_base_id,  # Modified
            'includeItemsFromAllDrives': True,  # Added
            'corpora': 'drive'  # Added
        }
    ).GetList()
    return element_list


def gdrive_folder_exists(drive: GoogleDrive, gdrive_base_id: str, gdrive_folder_id_to_search: str, folder_name: str):
    now_date = datetime.now()
    for gfile in gdrive_dir_list(drive, gdrive_base_id, gdrive_folder_id_to_search):
        if f"{folder_name}-{TODAY_DAY(now_date)}" in gfile["title"]:
            return gfile
    return None
