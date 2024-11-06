from PyQt5 import QtWidgets
from PyQt5.QtCore import QDate
from PyQt5.QtCore import QThread
from model_ import TabelModel, DataModel, Parser, BankModel, AccountModel
from pdf_convector import extract_and_process
from view_ import TableView, CategoriesView, ProgressBarView, InsertView
class LoginController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.setup_connections()

    def setup_connections(self):
        self.view.buttonBox.accepted.connect(self.ok_callback)

    def ok_callback(self):
        phone, password = self.view.lineEdit.text(), self.view.lineEdit_2.text()
        account = self.model.get_account(phone)
        status = self.model.validate_and_create_account(account, phone, password)

        if status == 'created':
            self.controller = InsertController(account)
            self.controller.show_insertView()
            self.view.hide()
        elif status == 'valid':
            self.controller = TableController(account)
            self.view.hide()
        elif status == 'invalid_format':
            QtWidgets.QMessageBox.information(self.view, 'Внимание', 'Неправильный формат пароля или телефона')
        elif status == 'invalid_password':
            QtWidgets.QMessageBox.information(self.view, 'Внимание', 'Неправильный пароль')


class InsertController:
        def __init__(self, account):
            self.model = BankModel()
            self.model2 = AccountModel()
            self.view = InsertView()
            self.account = account

            self.setup_connections()

        def setup_connections(self):
            self.view.buttonBox.accepted.connect(self.ok_callback)

        def ok_callback(self):

            if not self.view.lineEdit.text():
                QtWidgets.QMessageBox.information(self.view, 'Внимание', 'Введены не все значения')
            else:
                pdf_column_generator = list(extract_and_process(self.view.lineEdit.text()))
                self.controller = ProgressBarController(df=pdf_column_generator, account=self.account)
                self.controller.show_ProgressBarController()

        def show_insertView(self):
            self.view.show()

        def hide_insertView(self):
            self.view.hide()


class ProgressBarController:
        def __init__(self, df, account):
            self.df = df
            self.account = account

            self.view = ProgressBarView()
            self.view2 = InsertView()
            self.model = Parser(self.account['Пароль'], self.account['Телефон'], self.df)
            self.model2 = BankModel()
            self.model_thread = QThread()

            self.model.moveToThread(self.model_thread)
            self.model.progress.connect(self.view.update_progress)
            self.model.resultReady.connect(self.handle_result)
            self.model.error_occurred.connect(self.view.show_error)

            self.model_thread.started.connect(self.model.run)
            self.model_thread.start()

        def handle_result(self, result):
            try:
                self.model2.write_data(self.df, self.account['id'], result)
                self.controller = TableController(self.account)
                self.controller.show_tableview()
                self.view.hide()
            except:
                QtWidgets.QMessageBox.information(self.view, 'Внимание', 'Ошибка в записи данных')

        def show_ProgressBarController(self):
            self.view.show()


class TableController:
    def __init__(self,account):
        self.model = TabelModel()
        self.view = TableView()
        self.account = account

        self.initialize_view()
        self.setup_connections()

    def setup_connections(self):
        self.view.dateEdit.editingFinished.connect(self.update_dates)
        self.view.dateEdit_2.editingFinished.connect(self.update_dates)
        self.view.comboBox.currentIndexChanged.connect(self.on_combobox_changed)
        self.view.buttonBox.accepted.connect(self.filtration)

    def initialize_view(self):
        self.rows = self.model.fetch_account_statement_by_id(self.account['id'])
        self.db = self.model.read_finally_statement_by_id(self.account['id'])

        if len(self.rows) != 0:
            self.show_tableview()
            self.column_names = self.model.column_names()

            self.view.set_table_data(self.rows, self.column_names)

            min_date = QDate.fromString(self.db.iloc[0, 0].strftime('%d.%m.%Y'), "dd.MM.yyyy")
            max_date = QDate.fromString(self.db.iloc[-1, 0].strftime('%d.%m.%Y'), "dd.MM.yyyy")

            self.view.set_date_range(min_date, max_date)

        else:
            self.controller = InsertController(self.account)
            self.controller.show_insertView()
            QtWidgets.QMessageBox.information(self.view, 'Внимание', 'Данных не найдено')

    def update_dates(self):
        if self.view.dateEdit.date() > self.view.dateEdit_2.date():
            self.view.dateEdit_2.setMinimumDate(self.view.dateEdit.date())
        elif self.view.dateEdit.date() < self.view.dateEdit_2.date():
            self.view.dateEdit_2.setMinimumDate(self.view.dateEdit.date())

    def on_combobox_changed(self, index):
        self.selected_value = self.view.comboBox.itemText(index)