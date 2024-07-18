import pytesseract
from PIL import Image, ImageFilter, ImageDraw
from googletrans import Translator
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import fitz  # PyMuPDF
import os


def extract_hocr(image_path):
    try:
        # Open the image file
        image = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        return None

    try:
        # Perform OCR with HOCR output
        hocr = pytesseract.image_to_pdf_or_hocr(image, lang='eng', config='--psm 11', extension='hocr')
    except Exception as e:
        print(f"Error performing OCR: {e}")
        return None

    return hocr.decode('utf-8')


def extract_text(image_path):
    try:
        # Open the image file
        image = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        return None

    try:
        # Perform OCR to extract text
        text = pytesseract.image_to_string(image, lang='eng', config='--psm 11')
    except Exception as e:
        print(f"Error performing OCR: {e}")
        return None

    return text


def translate_text(text, target_language='hi'):
    translator = Translator()
    try:
        translated = translator.translate(text, dest=target_language)
    except Exception as e:
        print(f"Error translating text: {e}")
        return None
    return translated.text


def blur_text_background(image, word_boxes):
    # Create a mask image with the same size as the original image
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)

    # Draw white rectangles on the mask where the text is located
    for _, bbox in word_boxes:
        draw.rectangle(bbox, fill=255)

    # Blur the entire image
    blurred_image = image.filter(ImageFilter.GaussianBlur(10))

    # Composite the blurred image and the original image using the mask
    final_image = Image.composite(blurred_image, image, mask)

    return final_image


def create_pdf_with_images(image_path, hocr_text, translated_text, output_pdf_path):
    try:
        # Open the image file
        image = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # Extract word bounding boxes
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

    # Blur the text background
    image_with_blurred_text_bg = blur_text_background(image, word_boxes)

    # Create a new PDF with ReportLab
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter

    # Register the Hindi font
    # font_path = 'data/Mangal.ttf'  # Replace with the path to your Hindi font file
    # pdfmetrics.registerFont(TTFont('HindiFont', font_path))
    # c.setFont("HindiFont", 10)
    # Set the font to Helvetica
    c.setFont("Helvetica", 10)
    # Save the blurred image of the page
    img_path = "temp_image.png"
    image_with_blurred_text_bg.save(img_path)

    # Draw the blurred image
    c.drawImage(img_path, 0, 0, width, height)

    # Overlay translated text on the PDF
    translated_words = translated_text.split()
    for (original_word, bbox), translated_word in zip(word_boxes, translated_words):
        x1, y1, x2, y2 = bbox
        c.drawString(x1 * width / image.width, height - y2 * height / image.height, translated_word)

    c.showPage()
    c.save()

    # Clean up the temporary image
    os.remove(img_path)

    print(f"Translated PDF saved as {output_pdf_path}")


if __name__ == "__main__":
    pdf_name = "07 Adsolut coda.pdf"
    paths = os.listdir('data/images/' + pdf_name)
    for path in paths:
        print(path)
        input_image_path = "data/images/"+pdf_name+"/"+path  # Replace with your image file path
        target_language = "en"  # Replace with the target language code (e.g., 'hi' for Hindi)
        output_pdf_path = f"data/pdf/{pdf_name}/translated_output_{path}.pdf"  # Replace with desired output PDF file path

        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)  # Create the output directory if it doesn't exist

        hocr_text = extract_hocr(input_image_path)
        if hocr_text is None:
            print("Failed to extract HOCR text.")
            exit()

        text = extract_text(input_image_path)
        if text is None:
            print("Failed to extract text.")
            exit()

        translated_text = translate_text(text, target_language)
        if translated_text is None:
            print("Failed to translate text.",text)
            continue

        create_pdf_with_images(input_image_path, hocr_text, translated_text, output_pdf_path)
