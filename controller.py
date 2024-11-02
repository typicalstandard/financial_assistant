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




class TableController:
    pass