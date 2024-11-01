from PyQt5 import QtWidgets
from PyQt5.QtCore import QDate
from PyQt5.QtCore import QThread
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
    pass

class TableController:
    pass