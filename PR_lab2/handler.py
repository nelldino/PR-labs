from fastapi import FastAPI, UploadFile, File, HTTPException
import json

app = FastAPI()


# File upload endpoint
@app.post("/upload-json/")
async def upload_json_file(file: UploadFile = File(...)):
    if file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="Invalid file type. Only JSON files are accepted.")

    # Read the JSON content
    contents = await file.read()

    try:
        # Parse the JSON content to ensure it's valid
        json_data = json.loads(contents)
        return {"filename": file.filename, "json_content": json_data}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file.")
