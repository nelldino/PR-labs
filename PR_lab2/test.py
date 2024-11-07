import requests

url = "http://127.0.0.1:8000/upload-json/"
file_path = "books.json"  # replace with the actual file path

with open(file_path, "rb") as f:
    files = {"file": (file_path, f, "application/json")}
    response = requests.post(url, files=files)

print(response.json())
