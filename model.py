import psycopg2
import re
import csv
class Database:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'conn'):
            self.conn = psycopg2.connect(dbname='bank_statement', user='user', password='password', host='localhost')
            self.cursor = self.conn.cursor()

    def get_cursor(self):
        return self.cursor

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.cursor.close()



class AccountModel:
    def __init__(self):
        self.db = Database()
        self.cursor = self.db.get_cursor()

    def get_account(self, phone):
        query = "SELECT * FROM account WHERE account.Телефон = %s"
        self.cursor.execute(query, (phone,))
        row = self.cursor.fetchone()

        if row:
            columns = [desc[0] for desc in self.cursor.description]
            account_dict = dict(zip(columns, row))
            return account_dict
        return None

    def create_account(self, phone, password):
        insert_query = "INSERT INTO account (Телефон,Пароль) VALUES (%s, %s)"
        self.cursor.execute(insert_query, (phone, password))
        self.db.commit()

    def is_valid_phone(self, phone):
        pattern_phone = r"^\(\d{2}\) \d{3}-\d{2}-\d{2}$"
        return re.match(pattern_phone, phone)

    def is_valid_password(self, password):
        pattern_password = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)([a-zA-Z\d]){8,25}$"
        return re.match(pattern_password, password)

    def validate_and_create_account(self, account,phone, password):
        if account is None:
            if self.is_valid_phone(phone) and self.is_valid_password(password):
                self.create_account(phone, password)
                return 'created'
            else:
                return 'invalid_format'
        elif account['Пароль'] == password and account['Телефон'] == phone:
            return 'valid'
        else:
            return 'invalid_password'

class BankModel:
    def __init__(self):
        self.db = Database()
        self.cursor = self.db.get_cursor()

    def get_bank_statement_notes(self):
        query = "SELECT Примечание FROM bank_statement"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return rows

    def get_mcc_data(self):
        query = "SELECT * FROM mcc_bank"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    def write_bank_statement(self,processed_data, account_id):
        insert_bank_statement = """
        INSERT INTO bank_statement 
        (Дата, Примечание, Сумма_в_валюте_счета, Сумма_в_валюте_операции, account_id) 
        VALUES (%s, %s, %s, %s, %s)
        """

        try:
            for data in processed_data:
                for values in data.values():
                    self.cursor.execute(insert_bank_statement, tuple(values) + (account_id,))

        except Exception as e:
            print(f"Произошла ошибка при записи банковской выписки: {e}")
            return False
        return True

    def write_mcc_code(self, mcc_from_site):
            insert_mcc_code = "INSERT INTO mcc_bank (Примечание, MCC, Категория) VALUES (%s, %s, %s)"
            with open('csv/mcc_codes.csv', 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                mcc_codes = {row[0]: row[1] for row in reader}
                try:
                    for key in mcc_from_site:
                        self.cursor.execute(insert_mcc_code,
                                            (key, mcc_from_site[key], mcc_codes.get(mcc_from_site[key])))
                except Exception as e:
                    print(f"Произошла ошибка при записи кода MCC: {e}")
                    return False
            return True

    def write_finally_statement(self):
            try:
                join_query = """
                       INSERT INTO finally_statement (Дата,Примечание,MCC,Категория,Сумма_в_валюте_счета,Сумма_в_валюте_операции,account_id)
                       SELECT Дата,Примечание,MCC,Категория,Сумма_в_валюте_счета,Сумма_в_валюте_операции,account_id
                       FROM bank_statement
                       INNER JOIN mcc_bank USING (Примечание)
                       WHERE bank_statement.Примечание IS NOT NULL AND bank_statement.Дата IS NOT NULL
                       ORDER BY Дата;
                   """
                self.cursor.execute(join_query)

            except Exception as e:
                print(f"Произошла ошибка при записи финальной выписки: {e}")
                return False
            return True

    def write_data(self,processed_data,account_id, mcc_from_site):
            try:
                self.cursor.execute("BEGIN;")  # Начать транзакцию
                if not self.write_bank_statement(processed_data,account_id):
                    raise Exception("Ошибка при записи банковской выписки")
                if not self.write_mcc_code(mcc_from_site):
                    raise Exception("Ошибка при записи кода MCC")
                if not self.write_finally_statement():
                    raise Exception("Ошибка при записи финальной выписки")
                self.db.commit()
                print("Данные успешно записаны.")
            except Exception as e:
                print(f"Произошла ошибка: {e}")
                self.db.rollback()