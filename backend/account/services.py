def handle_upload_avatar(f):
    file_path = f"uploads/avatars/{f.name}"
    with open(file_path, "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path
