import re
import pdfplumber


def table_converter(table):
    return [[g.replace('\n', ' ') if not re.findall(r'[.:-]\n', g) else g.replace('\n', '') for g in i] for i in table]

def extract(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        tables = []
        for page in pdf.pages:
            all_tables = page.extract_tables()
            for table in all_tables:
                if len(table[0]) == 4:
                    title_table = table_converter(table)
                    tables.append(table_converter(table[1:]))
        return title_table[0], tables




