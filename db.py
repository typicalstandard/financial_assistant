import csv
import re
import warnings
warnings.filterwarnings("ignore", "\nPyarrow", DeprecationWarning)
import pandas as pd

def write_mcc_code(mcc_from_site, cursor):# нужно заменить на join
    insert_query = "INSERT INTO mcc_bank (Примечание, MCC, Категория) VALUES (%s, %s, %s)"
    with open('csv/mcc_codes.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        mcc_codes = {row[0]: row[1] for row in reader}
        for key in mcc_from_site:
            cursor.execute(insert_query, (key, mcc_from_site[key], mcc_codes.get(mcc_from_site[key])))


def write_bank_statement(recycle_table, cursor):
    insert = "INSERT INTO bank_statement (Дата,Примечание,Сумма_в_валюте_счета,Сумма_в_валюте_операции,account_id) VALUES (%s, %s, %s, %s,(select id from account ORDER BY id DESC LIMIT 1))"
    table = recycle_table[1]
    for row in table:
        for values in row:
            if len(values[1]) < 100:
                values[1] = re.sub(r'(?<!\w)[0-9]{8}(?!\w)', '', values[1].upper())
            elif  values[1].find('Заработная плата')  != -1 or values[1].find('Зарплата')  != -1 :
                values[1] = 'ЗП'
            cursor.execute(insert,values)


def reading(conn,sapros,phone):
    df = pd.read_sql(sapros, params={'value': phone}, con=conn)
    conn.close()
    return pandas(df)


def writing(conn,cursor,x):
             join_query = """
                    INSERT INTO finally_statement (Дата,Примечание,MCC,Категория,Сумма_в_валюте_счета,Сумма_в_валюте_операции,account_id)
                    SELECT Дата,Примечание,MCC,Категория,Сумма_в_валюте_счета,Сумма_в_валюте_операции,account_id
                    FROM bank_statement
                      INNER JOIN mcc_bank USING (Примечание)
                    WHERE bank_statement.Примечание IS NOT NULL AND bank_statement.Дата IS NOT NULL
                    ORDER BY Дата;
                    """
             cursor.execute(join_query)
             conn.commit()

             df = pd.read_sql(x, conn)
             conn.close()
             return pandas(df)

def pandas(df):
    df['Дата'] = pd.to_datetime(df['Дата'], format="%d.%m.%Y")

    def check_number(x):
        try:
            num = float(x.split()[0])
            return num
        except:
            return 0

    df.dropna(inplace=True)
    df['Сумма_в_валюте_счета'] = df['Сумма_в_валюте_счета'].apply(lambda x: check_number(x)).astype(float)
    df['Доходы/Расходы'] = df['Сумма_в_валюте_счета'].apply(lambda x: 'Расходы' if x < 0 else 'Доходы')
    df['Сумма_в_валюте_счета'] = df['Сумма_в_валюте_счета'].apply(lambda x: abs(x))
    return df
