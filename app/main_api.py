from translate_utility import translate_text, convert_pdf2docx
from time import sleep
import os
# converted_file = convert_pdf2docx("charges-deductibles-brochure-202404.pdf")
# print(f"Converted file saved to: {converted_file}")
#
# sleep(1)
# translated_file = translate_text(converted_file, "nl")
# print(f"Translated file saved to: {translated_file}")
from typing import Union

from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app_api = FastAPI()

origins = [
    "http://http://127.0.0.1:8000",
    "https://http://127.0.0.1:8000",
    "http://localhost",
    "http://localhost:8080",
]

app_api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from enum import Enum
from googletrans import LANGUAGES


class Language(str, Enum):
    hindi = "hi"
    english = "en"
    dutch = "nl"
    french = "fr"
    japanese = "ja"
    russian = "ru"
    arabic = "ar"


languages = {
    "Language.english": "en",
    "Language.dutch": "nl",
    "Language.french": "fr",
    "Language.japanese": "ja",
    "Language.russian": "ru",
    "Language.hindi": "hi",
    "Language.arabic": "ar"
}


@app_api.get("/")
def read_root():
    return {"Message": "Translate api"}


@app_api.post("/upload/")
# @app_api.post("/upload")
async def upload_file(file: UploadFile):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Please upload a PDF file!!")

    file_location = f"data/input/{file.filename}"

    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_location), exist_ok=True)

    with open(file_location, "wb") as f:
        content = await file.read()  # Read the file content
        f.write(content)  # Write the content to the file

    return {
        "pdf_name": file.filename,
        "Content-Type": file.content_type,
        "file_location": file_location,
        "file_size": f"{file.size / 1_048_576:.2f}",

    }


@app_api.get("/list_files")
@app_api.get("/list_files/")
def list_dirs():
    # print(os.listdir("data/input"))
    data = os.listdir("data/input")
    return {"file_list": data}


@app_api.post("/pdf2docx/{file_name}")
def convertpdf(file_name: str):
    path = os.path.join("data/input", file_name)
    docx_path = os.path.normpath(path)

    if not os.path.isfile(docx_path):
        return {"message": "File not found!"}
    docx_path = convert_pdf2docx(file_name)
    return {"docx_path": docx_path}


@app_api.post("/docx2pdf/{file_name}/{lang}")
def translate(file_name: str, lang: Language):
    path = os.path.join("data/output", file_name)
    docx_path = os.path.normpath(path)

    if not os.path.isfile(docx_path):
        return {"message": "File not found!"}
    path = translate_text(docx_path, target_language=lang.value)
    return {"docx_path": path}
