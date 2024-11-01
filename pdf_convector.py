import re
import pdfplumber

def table_converter(table):
    return [
        [cell.replace('\n', ' ') if not re.search(r'[.:-]\n', cell) else cell.replace('\n', '') for cell in row]
        for row in table
    ]

def extract_and_process(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            all_tables = page.extract_tables()
            for table in all_tables:
                if len(table[0]) == 4:
                    yield from table_converter(table[1:])

