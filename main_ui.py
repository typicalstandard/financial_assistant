from PyQt5.Qt import *
from PyQt5.QtCore import  Qt
from pdf_convert_csv import extract
from parsing_mcc import Parser
from db import write_mcc_code, write_bank_statement
import matplotlib
from PyQt5 import  QtWidgets
import re
matplotlib.use('Qt5Agg')
from ui import Ui_Login, Ui_Form, Ui_Table
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import random
from db import writing,reading
import warnings

warnings.filterwarnings("ignore", "\nPyarrow", DeprecationWarning)
import psycopg2
import sys

conn = psycopg2.connect(dbname='bank_statement', user='pupa', password='123456', host='localhost')

cursor = conn.cursor()


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class Сategories(QtWidgets.QWidget):
    def __init__(self, formLayout, verticalLayout, db, first_date, last_date, income_expence='Расходы'):
        super(Сategories, self).__init__()
        self.formLayout = formLayout
        self.verticalLayout = verticalLayout
        self.db = db
        self.first_date = first_date
        self.last_date = last_date
        self.income_expence = income_expence
        sc = MplCanvas(self, width=5, height=4, dpi=100)

        def color_generation():
            r = lambda: random.randint(0, 255)
            colors = '#%02X%02X%02X' % (r(), r(), r())
            return colors

        _df = self.db.groupby(
            self.db['Категория'][
                self.db['Дата'].between(self.first_date, self.last_date) & (
                        self.db['Доходы/Расходы'] == self.income_expence)])[
            'Сумма_в_валюте_счета'].sum().sort_values(ascending=False)


        if len(_df) != 0:
            df_categories = _df.iloc[:7]
            if len(_df) > 7:
                df_categories.loc["Прочее"] = _df[_df < df_categories.iloc[-1]].sum()

            colors = []

            for col_name, data in df_categories.items():
                color = color_generation()
                colors.append(color)
                pbar = QProgressBar()
                pbar.setRange(0, int(_df.max()))
                pbar.setStyleSheet(f"QProgressBar::chunk {{background-color: {color} }}")
                pbar.setValue(int(data))
                pbar.setFormat(f'{int(data)}')
                pbar.setAlignment(Qt.AlignRight)
                self.formLayout.addRow(col_name, pbar)


            data = [float(i) for i in df_categories.tolist()]
            ab = df_categories.plot(ax=sc.axes)
            ab.pie(data, colors=colors, wedgeprops={"edgecolor": "black",
                                                    'linewidth': 1,
                                                    'antialiased': True})
            self.verticalLayout.addWidget(sc)

        else:
            self.label = QLabel("Нет данных")
            self.label.setAlignment(Qt.AlignCenter)
            self.formLayout.addRow(self.label)


class Table(QtWidgets.QWidget, Ui_Table):
    def __init__(self,phone,check):
        super(Table, self).__init__()
        self.setupUi(self)
        self.phone = phone
        self.check  = check


        Frame.hide()

        if self.check == None:
            x = """select * from finally_statement where finally_statement.account_id = (select account.id from account ORDER BY id DESC limit 1);"""
            self.db = writing(conn,cursor,x)
            cursor.execute(x)
            rows = cursor.fetchall()
        else:
            d = "select * from finally_statement where finally_statement.account_id = (select id  from account where account.Телефон = %(value)s)"
            self.db = reading(conn,d,self.phone)
            cursor.execute(d, {'value': self.phone})  
            rows = cursor.fetchall()

        self.tableWidget.setRowCount(len(rows))
        self.tableWidget.setColumnCount(len(rows[0]))

        column_names = [desc[0] for desc in cursor.description]
        self.tableWidget.setHorizontalHeaderLabels(column_names)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        # Заполнение таблицы данными
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))

        min_date = QDate.fromString(self.db.iloc[0, 0].strftime('%d.%m.%Y'), "dd.MM.yyyy")
        max_date = QDate.fromString(self.db.iloc[-1, 0].strftime('%d.%m.%Y'), "dd.MM.yyyy")

        self.dateEdit.setMinimumDate(min_date)
        self.dateEdit.setMaximumDate(max_date)
        self.dateEdit_2.setMinimumDate(min_date)
        self.dateEdit_2.setMaximumDate(max_date)



        Сategories(self.formLayout, self.verticalLayout, self.db, self.db.iloc[0, 0].strftime('%d.%m.%Y'),
                   self.db.iloc[-1, 0].strftime('%d.%m.%Y'))

        self.first = self.dateEdit.date()
        self.last = self.dateEdit_2.date()

        self.dateEdit.editingFinished.connect(self.update)
        self.dateEdit_2.editingFinished.connect(self.update)
        self.comboBox.currentIndexChanged.connect(self.on_combobox_changed)
        self.buttonBox.accepted.connect(self.ok)

    def update(self):

        if self.dateEdit.date() > self.dateEdit_2.date():
            self.dateEdit_2.setMinimumDate(self.dateEdit.date())
        elif self.dateEdit.date() < self.dateEdit_2.date():
            self.dateEdit_2.setMinimumDate(self.dateEdit.date())
        self.first = self.dateEdit.date()
        self.last = self.dateEdit_2.date()

    def on_combobox_changed(self, index):
        self.selected_value = self.comboBox.itemText(index)

    def filtration(self):
        while self.formLayout.count():
            child = self.formLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if self.verticalLayout.count() != 0:
            child = self.verticalLayout.takeAt(0)
            child.widget().deleteLater()

        Сategories(self.formLayout, self.verticalLayout, self.db, self.first.toString('yyyy-MM-dd'),
                   self.last.toString('yyyy-MM-dd'), self.selected_value)


class ProgressBar(QWidget):
    def __init__(self, password, phone, df,check):
        super().__init__()
        self.password = password
        self.phone = phone
        self.df = df
        self.check = check
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.progressBar = QProgressBar(self)
        layout.addWidget(self.progressBar)

        self.worker = Parser(self.password, self.phone, self.df)
        self.worker.progress.connect(self.progressBar.setValue)
        self.worker.resultReady.connect(self.handleResult)
        self.worker.error_occurred.connect(self.handle_error)  # Подключение сигнала к слоту
        self.worker.start()
        self.setLayout(layout)

    def handle_error(self,error_message):

        self.hide()
        QtWidgets.QMessageBox.information(
            self, 'Внимание',error_message )


    def handleResult(self, result):
        write_mcc_code(result, cursor)
        self.k = Table(self.phone,self.check)
        self.k.show()
        self.hide()


class Login(QtWidgets.QWidget, Ui_Login):
    def __init__(self):
        super(Login, self).__init__()
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.ok_callback)
        self.buttonBox.rejected.connect(self.cancel_callback)

    def cancel_callback(self):
        self.lineEdit.clear()
        self.lineEdit_2.clear()

    def ok_callback(self):
        phone, password = self.lineEdit.text(), self.lineEdit_2.text()
        self.check = self.get_account(phone)

        if self.check is None:
            if self.is_valid_phone(phone) and self.is_valid_password(password):
                self.create_account(phone, password)
                self.x = Insert(phone, password, self.check)
                self.x.show()
                self.hide()
            else:
                QtWidgets.QMessageBox.information(
                    self, 'Внимание', 'Неправильный формат пароля или телефона')
        elif self.check and self.check[-1] == password:
            self.c = Table(phone, self.check)
            self.c.show()
        else:
            QtWidgets.QMessageBox.information(
                self, 'Внимание', 'Неправильный пароль')

    def get_account(self, phone):
        query = "SELECT * FROM account WHERE account.Телефон = %s"
        cursor.execute(query, (phone,))
        return cursor.fetchone()

    def is_valid_phone(self, phone):
        pattern_phone = r"^\(\d{2}\) \d{3}-\d{2}-\d{2}$"
        return re.match(pattern_phone, phone)

    def is_valid_password(self, password):
        pattern_password = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%&*()_\-+.:])([a-zA-Z\d!@#$%&*()_\-+.:]){8,25}$"
        return re.match(pattern_password, password)

    def create_account(self, phone, password):
        insert_query = "INSERT INTO account (Телефон, Пароль) VALUES (%s, %s)"
        cursor.execute(insert_query, (phone, password))


class Insert(QWidget, Ui_Form):
    def __init__(self, phone, password, check):
        super(Insert, self).__init__()
        self.setupUi(self)
        self.phone = phone
        self.password = password
        self.check = check

        self.pushButton.clicked.connect(self.input_pdf)
        self.buttonBox.accepted.connect(self.ok_callback)
        self.buttonBox.rejected.connect(self.cancel_callback)

    def input_pdf(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Save File', './', "PDF Files (*.pdf)")
        self.lineEdit.setText(file)

    def cancel_callback(self):
        self.lineEdit.clear()

    def ok_callback(self):
        if not self.lineEdit.text():
            QtWidgets.QMessageBox.information(
                self, 'Внимание', 'Введены не все значения')
        else:
            try:
                pdf = extract(str(self.lineEdit.text()))
                write_bank_statement(pdf, cursor)
                rows_set = self.get_bank_statement_notes()
                mcc_data = self.get_mcc_data()

                if mcc_data:
                    good = rows_set ^ set((i[1] for i in mcc_data))
                    if not good:
                        self.show_table()
                    else:
                        self.show_progress_bar(good)
                else:
                    self.show_progress_bar(rows_set)
            except Exception as e:
                print(f"Произошла ошибка: {e}")
                QtWidgets.QMessageBox.information(
                    self, 'Внимание', 'Ошибка')

    def get_bank_statement_notes(self):
        query = "SELECT Примечание FROM bank_statement"
        cursor.execute(query)
        rows = cursor.fetchall()
        return set(row[0] for row in rows)

    def get_mcc_data(self):
        query = "SELECT * FROM mcc_bank"
        cursor.execute(query)
        return cursor.fetchall()

    def show_table(self):
        self.b = Table(self.phone, self.check)
        self.b.show()

    def show_progress_bar(self, data):
        self.x = ProgressBar(self.password, self.phone, data, self.check)
        self.x.show()



import traceback


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)

    text += ''.join(traceback.format_tb(tb))

    QtWidgets.QMessageBox.critical(None, 'Error', text)

    sys.exit()


sys.excepthook = log_uncaught_exceptions

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Frame = Login()
    Frame.show()
    sys.exit(app.exec_())
