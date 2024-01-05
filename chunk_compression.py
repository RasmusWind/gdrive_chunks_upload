import os
import zipfile
from progressbar import ProgressBar


MAX_CHUNK_SIZE = 2 * 1024 * 1024 * 1024 # 10 GigaBytes
COMPRESSION_MODE = zipfile.ZIP_DEFLATED


def dir_to_size_dict(dir_path): # converts a directory into a dictionary, where the keys are the folder/file name and the key is the size
    dir_elements = os.listdir(dir_path)
    dir_dict = {}
    for de in dir_elements:
        if os.path.isdir(f"{dir_path}/{de}"):
            dir_dict[de] = get_folder_size(f"{dir_path}/{de}")
            continue
        dir_dict[de] = os.path.getsize(f"{dir_path}/{de}")
    return dir_dict    


def chunksize_path(dir_path): # Converts a path into chunks of size MAX_CHUNK_SIZE. It does this recursively, meaning if a subfolder has a size bigger than MAX_CHUNK_SIZE, it will chunksize the subfolders content, and so on. 
    d = dir_to_size_dict(dir_path)
    chunks = {}
    chunk = []
    current_chunk_size = 0
    items = d.items()
    for ind, (element, size) in enumerate(items):
        if size < MAX_CHUNK_SIZE and current_chunk_size < MAX_CHUNK_SIZE:
            chunk.append(element)
            current_chunk_size += size
        elif current_chunk_size >= MAX_CHUNK_SIZE:
            if dir_path in chunks:
                chunks[dir_path].append(chunk)
            else:
                chunks[dir_path] = [chunk]
            chunk = [element]
            current_chunk_size = size
        elif size >= MAX_CHUNK_SIZE:
            if os.path.isdir(f"{dir_path}/{element}"):
                if dir_path in chunks:
                    chunks[dir_path].append(chunksize_path(f"{dir_path}/{element}"))
                else:
                    chunks[dir_path] = [chunksize_path(f"{dir_path}/{element}")]
            else:
                if dir_path in chunks:
                    chunks[dir_path].append(element)
                else:
                    chunks[dir_path] = [element]
        if ind == len(items) - 1:
            if dir_path in chunks:
                chunks[dir_path].append(chunk)
            else:
                chunks[dir_path] = [chunk]

    return chunks


def compress_chunks(chunks_dict:dict, pb:ProgressBar=None, root=True) -> str|None:
    new_path = ""
    for folder_path, chunks in chunks_dict.items():
        folder_path_split = os.path.split(folder_path)
        parent_path = os.path.join(*folder_path_split[:-1])
        if not root:
            parent_path = f"{parent_path}_backup"
        folder_name = folder_path_split[-1]
        new_folder_name = f"{folder_name}_backup"

        new_path = os.path.join(parent_path, new_folder_name)
        os.mkdir(new_path)

        chunk_count = 1
        for chunk in chunks:
            if isinstance(chunk, list): #Chunk is a 1D list and all elements within needs to be zipped. 
                zfile = zipfile.ZipFile(os.path.join(new_path, f"chunk_{chunk_count}.zip"), mode="w")

                single = MAX_CHUNK_SIZE / len(chunk)
                single_percent = single / MAX_CHUNK_SIZE
                try:
                    for ind, chunk_file in enumerate(chunk):
                        file_path = os.path.join(folder_path, chunk_file)
                        if os.path.isdir(file_path):
                            zipfolder(f"{file_path}_backup", file_path)
                            chunk_file = f"{chunk_file}_backup.zip"
                            zfile.write(os.path.join(folder_path, chunk_file), chunk_file, compress_type=COMPRESSION_MODE)
                            os.remove(os.path.join(folder_path, chunk_file))
                        else:
                            zfile.write(os.path.join(folder_path, chunk_file), chunk_file, compress_type=COMPRESSION_MODE)
                        if pb:
                            pb.increment_progress(single_percent)
                except FileNotFoundError as e:
                    print("File not found")
                    print(e)
                finally:
                    zfile.close()
                chunk_count += 1
            elif isinstance(chunk, dict): #Chunk is a folder containing elements with a collective size over the MAX_CHUNK_SIZE limit.
                compress_chunks(chunk, pb=pb, root=False)
            else: # Chunk is a single file with a size above the MAX_CHUNK_SIZE limit.
                zfile = zipfile.ZipFile(os.path.join(new_path, f"chunk_{chunk_count}.zip"), mode="w")
                try:
                    zfile.write(os.path.join(folder_path, chunk), chunk, compress_type=COMPRESSION_MODE)
                except FileNotFoundError:
                    print("File not found")
                finally:
                    zfile.close()
                    if pb:
                        pb.increment_progress()
                chunk_count += 1

    if root:
        return new_path
    else:
        return None


def compress_path(dir_path: str) -> str|None:
    chunks = chunksize_path(dir_path)
    total = total_chunk_amount(chunks)
    pb = ProgressBar("COMPRESSING: ", 0, total, True)
    new_path = compress_chunks(chunks, pb=pb, root=True)
    return new_path


def total_chunk_amount(chunks_dict):
    amount = 0
    for path, content in chunks_dict.items():
        for item in content:
            if isinstance(item, dict):
                amount += total_chunk_amount(item)
            else:
                amount += 1
    return amount


def zipfolder(foldername, target_dir):            
    zipobj = zipfile.ZipFile(foldername + '.zip', 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(target_dir) + 1
    for base, dirs, files in os.walk(target_dir):
        for file in files:
            fn = os.path.join(base, file)
            zipobj.write(fn, fn[rootlen:])


def get_folder_size(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size