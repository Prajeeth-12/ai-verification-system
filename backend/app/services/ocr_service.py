import easyocr
import fitz
from PIL import Image
import io

reader = easyocr.Reader(['en'])

def extract_text_from_image(image_path):

    results = reader.readtext(image_path)

    extracted_text = " ".join([text[1] for text in results])

    return extracted_text


def extract_text_from_pdf(pdf_path):

    doc = fitz.open(pdf_path)

    full_text = ""

    for page_num in range(len(doc)):

        page = doc.load_page(page_num)

        pix = page.get_pixmap()

        img_bytes = pix.tobytes("png")

        image = Image.open(io.BytesIO(img_bytes))

        temp_image_path = "temp_page.png"

        image.save(temp_image_path)

        text = extract_text_from_image(temp_image_path)

        full_text += text + "\n"

    return full_text
