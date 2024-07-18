import re
import os
import fitz  # PyMuPDF

import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from config import UPLOAD_DIRECTORY, IMAGE_DIRECTORY, PDF_DIRECTORY

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from concurrent.futures import ThreadPoolExecutor


def save_image(image, image_path, quality=95):
    image.save(image_path, 'PNG', quality=quality)
    print(f"Image saved: {image_path}")


def pdf_to_images(pdf_name: str, dpi=300, quality=95, max_workers=4):
    try:

        # Path to the PDF file
        pdf_path = os.path.join(UPLOAD_DIRECTORY, pdf_name)
        pdf_path = os.path.normpath(pdf_path)

        pdf_dir = os.path.splitext(pdf_name)[0]

        output_dir = os.path.join(IMAGE_DIRECTORY, pdf_dir)
        output_dir = os.path.normpath(output_dir)

        os.makedirs(output_dir, exist_ok=True)

        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=dpi)
        image_paths = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, image in enumerate(images):
                image_path = os.path.join(output_dir, f"page_{i + 1}.png")
                image_paths.append(image_path)
                futures.append(executor.submit(save_image, image, image_path, quality))

            for future in futures:
                future.result()  # Wait for all threads to complete

        return output_dir, pdf_dir
    except Exception as e:
        print(e)


def image_to_pdf(image_folder: str, img_name: str) -> str:
    """
    Convert an image to a PDF using OCR.
    """
    try:
        image_path = os.path.join(image_folder, img_name)
        file_name = os.path.splitext(img_name)[0]

        # Open the image file
        image = Image.open(image_path)
        pdf_name = image_folder.split("\\")[-1]

        # Perform OCR and save the output as a PDF
        pdf_folder = os.path.join(PDF_DIRECTORY, pdf_name)
        # pdf_folder = os.path.join(PDF_DIRECTORY,  f"{file_name}.pdf")
        os.makedirs(pdf_folder, exist_ok=True)
        pdf_folder = os.path.normpath(pdf_folder)

        with open(pdf_folder + "/" + file_name + ".pdf", 'wb') as f:
            f.write(pytesseract.image_to_pdf_or_hocr(image, lang='eng', config='--psm 11', extension='pdf'))

        print(f"PDF saved: {pdf_folder}")
        return pdf_folder
    except Exception as e:
        print(f"Failed to convert image to PDF: {e}")
        raise


def numerical_sort(value):
    parts = re.split(r'(\d+)', value)
    return [int(part) if part.isdigit() else part for part in parts]


def combine_pdfs(pdf_directory, pdf_name):
    # Directory containing the PDF files
    # pdf_directory = 'static/pdf/' + pdf_name

    # List and sort PDF files
    file_paths = ([os.path.join(pdf_directory, f) for f in os.listdir(pdf_directory) if f.endswith('.pdf')])
    pdf_files = sorted(file_paths, key=numerical_sort)
    print(pdf_files, end='\n')
    # Output file path
    output_pdf = f'static/output/combined_{pdf_name}.pdf'

    # Create a new PDF document
    combined_pdf = fitz.open()

    # Loop through each sorted PDF file
    for pdf_file in pdf_files:
        # Open the current PDF file
        pdf_document = fitz.open(pdf_file)
        # Iterate through each page
        for page_num in range(len(pdf_document)):
            # Get the page
            page = pdf_document.load_page(page_num)
            # Add the page to the combined PDF
            combined_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
        pdf_document.close()

    # Save the combined PDF to a file
    combined_pdf.save(output_pdf)
    combined_pdf.close()

    print(f"Combined PDF saved to {output_pdf}")
    return output_pdf


def create_pdf_with_images(image_path, hocr_text, translated_text, output_pdf_path):
    # Open the original image with PyMuPDF
    image = Image.open(image_path)
    pix = fitz.Pixmap(image_path)

    # Create a new PDF with ReportLab
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter

    # Save the image of the page
    img_path = "temp_image.png"
    pix.save(img_path)

    # Draw the image
    c.drawImage(img_path, 0, 0, width, height)

    # Overlay translated text on the PDF
    translated_words = translated_text.split()
    word_boxes = []
    lines = hocr_text.split('\n')

    for line in lines:
        if 'bbox ' in line and 'ocrx_word' in line:
            try:
                bbox = line.split('bbox ')[1].split(';')[0]
                bbox = list(map(int, bbox.split()))
                word = line.split('>')[1].split('<')[0]
                word_boxes.append((word, bbox))
            except (IndexError, ValueError):
                continue

    c.setFont("Helvetica", 10)
    for (original_word, bbox), translated_word in zip(word_boxes, translated_words):
        x1, y1, x2, y2 = bbox
        c.drawString(x1 * width / pix.width, height - y2 * height / pix.height, translated_word)

    c.showPage()
    c.save()

    # Clean up the temporary image
    os.remove(img_path)

    print(f"Translated PDF saved as {output_pdf_path}")
