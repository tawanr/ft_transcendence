import os


def handle_upload_avatar(f):
    file_path = f"uploads/avatars/{f.name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path
