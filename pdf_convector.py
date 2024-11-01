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
                    yield from process_table(table_converter(table[1:]))

def process_table(tables):
    for row in tables:
        for values in row:
            if len(values) > 1:
                if len(values[1]) < 100:
                    values[1] = re.sub(r'(?<!\w)[0-9]{8}(?!\w)', '', values[1].upper())
                elif 'Заработная плата' in values[1] or 'Зарплата' in values[1]:
                    values[1] = 'ЗП'
                if values[1] != '':
                    yield values

pdf_path = 'your_pdf_path_here.pdf'
processed_data = list(extract_and_process(pdf_path))
