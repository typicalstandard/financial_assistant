from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QProgressBar, QVBoxLayout, QMessageBox
from ui import Ui_Login, Ui_Form, Ui_Table

class LoginView(QtWidgets.QWidget, Ui_Login):
    def __init__(self):
        super(LoginView, self).__init__()
        self.setupUi(self)

        self.buttonBox.rejected.connect(self.cancel_callback)

    def cancel_callback(self):
        self.lineEdit.clear()
        self.lineEdit_2.clear()
        self.lineEdit_2.clear()

class InsertView(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(InsertView, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.input_pdf)
        self.buttonBox.rejected.connect(self.cancel_callback)

    def input_pdf(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Save File', './', "PDF Files (*.pdf)")
        self.lineEdit.setText(file)

    def cancel_callback(self):
        self.lineEdit.clear()

class ProgressBarView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.progressBar = QProgressBar(self)
        layout.addWidget(self.progressBar)
        self.setLayout(layout)

