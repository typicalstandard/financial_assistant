import psycopg2
import re
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
