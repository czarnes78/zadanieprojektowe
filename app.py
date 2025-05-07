from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from langdetect import detect, detect_langs
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os
import csv

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

LOG_FILE = "detections_log.csv"

@app.get("/", response_class=HTMLResponse)
def root():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()

class TextInput(BaseModel):
    text: str

@app.post("/detect_language")
def detect_language(input: TextInput):
    try:
        lang = detect(input.text)
        all_langs = detect_langs(input.text)
        log_detection(input.text, lang)
        return {
            "language": lang,
            "candidates": [str(l) for l in all_langs]
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode("utf-8")
        lang = detect(text)
        log_detection(text[:100], lang)
        return {"filename": file.filename, "language": lang}
    except Exception as e:
        return {"error": str(e)}

@app.get("/history")
def get_history():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)[-10:]

def log_detection(text, language):
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(["timestamp", "language", "text"])
        writer.writerow([datetime.utcnow().isoformat(), language, text.replace('\n', ' ')[:100]])
