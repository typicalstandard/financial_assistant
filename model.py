import psycopg2
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PyQt5.QtCore import QObject, pyqtSignal
import time

import csv

from sqlalchemy import create_engine


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

class Parser(QObject):
    progress = pyqtSignal(int)
    resultReady = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, password, phone, df):
        super().__init__()

        self.db = Database()
        self.cursor = self.db.get_cursor()
        self.password = password
        self.phone = phone
        self.df = df

    def run(self):
        mcc_from_site = dict()
        options = Options()
        with webdriver.Firefox(options=options) as driver:
                wait = WebDriverWait(driver, 10)
                self.login(driver, wait)
                time.sleep(4)
                self.navigate_to_history(driver, wait)
                time.sleep(1)
                self.extract_mcc_codes(driver, wait, mcc_from_site)
                time.sleep(2)
                self.resultReady.emit(mcc_from_site)


    def login(self, driver, wait):
        driver.get("https://insnc.by/")
        user_name = wait.until(EC.presence_of_element_located((By.NAME, 'phone')))
        user_name.send_keys(self.phone, Keys.RETURN)
        user_password = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        user_password.send_keys(self.password, Keys.RETURN)

    def navigate_to_history(self, driver, wait):
        history = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/history']")))
        history.click()

    def extract_mcc_codes(self, driver, wait, mcc_from_site):
        x = 100 / 20
        self.s = [0]
        for column_table in self.df:
          for name in column_table.keys():
            next_term = self.s[-1] + x
            self.s.append(next_term)
            self.progress.emit(int(next_term))
            try:
                shopping_list = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@data-test-id='historyCell']")))
                original_text = shopping_list.text
                search = wait.until(EC.element_to_be_clickable((By.NAME, 'searchText')))
                search.send_keys(name, Keys.RETURN)
                check = wait.until_not(
                    EC.text_to_be_present_in_element((By.XPATH, "//button[@data-test-id='historyCell']"),
                                                     original_text))
                if check:
                    updated_shopping_list = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@data-test-id='historyCell']")))
                    updated_shopping_list.click()
                self.parse_side_panel(wait, mcc_from_site, name)
                search.clear()
            except Exception as e:
                mcc_from_site[name] = 0
                search.clear()
                self.error_occurred.emit(f"Error processing {name}: {str(e)}")

    def parse_side_panel(self, wait, mcc_from_site, name):
        try:
            side_panel = wait.until(EC.visibility_of_element_located((
                By.XPATH, "//div[@class='history-details-side-panel_mainContent__gnt+e']"))).text.split()
            if side_panel[13].isdigit():
                mcc_from_site[name] = side_panel[13]
            else:
                mcc_from_site[name] = 0
        except Exception as e:
            mcc_from_site[name] = 0
            self.error_occurred.emit(f"Error parsing side panel for {name}: {str(e)}")


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

class TabelModel:
    def __init__(self):
        self.db = Database()  # Используем Singleton для подключения к БД
        self.cursor = self.db.get_cursor()
        self.engine = create_engine('подключение к бд')

