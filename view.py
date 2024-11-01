from PyQt5 import QtWidgets
from ui import Ui_Login, Ui_Form, Ui_Table

class LoginView(QtWidgets.QWidget, Ui_Login):
    def __init__(self):
        super(LoginView, self).__init__()
        self.setupUi(self)

        self.buttonBox.rejected.connect(self.cancel_callback)

    def cancel_callback(self):
        self.lineEdit.clear()
        self.lineEdit_2.clear()