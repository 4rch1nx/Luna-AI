import PyPDF2

def pdf_to_text(pdf_path, txt_path):
    try:
        with open(pdf_path, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            full_text = ""

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n\n"

            with open(txt_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(full_text)

            print(f"Successfully converted '{pdf_path}' to '{txt_path}'")
    except Exception as e:
        print(f"Error converting PDF: {e}")
