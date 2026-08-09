import sys
try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not installed. Try pip install pypdf2")
    sys.exit(1)

def extract_text(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            print(f"--- TEXT FROM {pdf_path} ---")
            print(text[:1000])  # Just print the first 1000 characters
            print("...")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

if __name__ == "__main__":
    extract_text("data/damodaran/raw/debt regression.pdf")
    extract_text("data/damodaran/raw/global regression debt.pdf")
