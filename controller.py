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


class InsertController:
    pass

class TableController:
    pass