import os
import shutil

from enum import Enum

from config import IMAGE_DIRECTORY
from img_pdf2pdf import pdf_to_images, image_to_pdf, combine_pdfs

from fastapi import FastAPI, UploadFile, HTTPException, Request, Form

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

origins = [
    "http://http://127.0.0.1:8000",
    "https://http://127.0.0.1:8000",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


UPLOAD_FOLDER = "static/uploads_pdf"


@app.post("/upload_file", response_class=HTMLResponse)
async def upload_pdf_file(request: Request, pdf_file: UploadFile):
    if pdf_file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported!")

    file_name = pdf_file.filename
    print(file_name)
    file_path = os.path.join(UPLOAD_FOLDER, file_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        with open(file_path, "wb+") as buffer:
            # shutil.copyfileobj(pdf_file.file, buffer)
            buffer.write(await pdf_file.read())

        # filepath = os.path.join(UPLOAD_FOLDER, file_name)

    except Exception as e:
        print("except", e)
    return templates.TemplateResponse("view.html", {"request": request,"image_name": file_name})


@app.post("/ocr", response_class=HTMLResponse)
async def ocr(request: Request, image_name: str = Form(...)):
    global combined_pdf, original_pdf
    original_pdf = image_name
    try:
        image_folder, pdf_dir = pdf_to_images(image_name)
        print(f"images are saved in this location: {image_folder}")
        output_dir = os.path.join(IMAGE_DIRECTORY, os.path.splitext(image_name)[0])
        output_dir = os.path.normpath(output_dir)

        image_files = os.listdir(output_dir)

        # print(image_files,"im")
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(image_to_pdf, image_folder, img_file) for img_file in image_files]
            results = [future.result() for future in futures]

        combined_pdf = combine_pdfs(results[0], pdf_dir)
        print(combined_pdf)
    except Exception as e:
        print(e)
    return templates.TemplateResponse("pdf_view.html",
                                      {"request": request, "image_name": image_name,
                                       "pdf": combined_pdf})


@app.get("/ocr", response_class=HTMLResponse)
async def ocr_get(request: Request):
    return templates.TemplateResponse("pdf_view.html",
                                      {"request": request, "image_name": original_pdf,
                                       "pdf": combined_pdf})
