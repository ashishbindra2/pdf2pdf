from googletrans import Translator
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os


def pdf2image(pdf_name):
    # Path to the PDF file
    pdf_path = f'data/input/{pdf_name}'

    # Directory to save the image
    # data = pdf_path.split('/')[-1]

    output_dir = 'data/images/' + pdf_name
    os.makedirs(output_dir, exist_ok=True)

    # Convert PDF to images
    images = convert_from_path(pdf_path, dpi=300)

    # Save each page as an image
    for i, image in enumerate(images):
        image_path = f"{output_dir}/page_{i + 1}.png"
        image.save(image_path, 'PNG', quality=95)
        print(f"Saved {image_path}")


# pdf2image("07 Adsolut coda.pdf")


def image_to_pdf(image_path: str, file_name):
    # Set the path to the Tesseract executable
    pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'  # Update this path based on your Tesseract installation

    # Open the image file
    image = Image.open('data/images/' + image_path + "/" + file_name)

    # Perform OCR and save the output as a PDF
    text = pytesseract.image_to_string(image, lang='eng', config='--psm 11')
    print(text)
    os.makedirs('data/pdf/' + image_path, exist_ok=True)
    # Save the PDF file
    with open('data/pdf/' + image_path + "/" + file_name.replace(".png", ".pdf"), 'wb') as f:
        f.write(pytesseract.image_to_pdf_or_hocr(image, lang='eng', config='--psm 11', extension='pdf'))
        f.write(text.encode('utf-8'))


# pdf_name = "07 Adsolut coda.pdf"
pdf_name = "Holidays.pdf"
paths = os.listdir('data/images/' + pdf_name)
for path in paths:
    print(path)
    image_to_pdf(pdf_name, path)


# image_to_pdf("Holidays.pdf","page_1.png")

def combine_pdfs(pdf_name):
    # Directory containing the PDF files
    pdf_directory = 'data/pdf/' + pdf_name
    print(pdf_directory)
    # List and sort PDF files
    pdf_files = sorted([os.path.join(pdf_directory, f) for f in os.listdir(pdf_directory) if f.endswith('.pdf')])

    # Output file path
    output_pdf = f'data/output/combined_{pdf_name}.pdf'

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


# combine_pdfs(pdf_name)

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


# create_pdf_with_images("data/images/Holidays.pdf/page_1.png", )
