from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QProgressBar, QVBoxLayout, QMessageBox, QTableWidgetItem
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

class TableView(QtWidgets.QWidget,Ui_Table):
    def __init__(self):
        super(TableView, self).__init__()
        self.setupUi(self)


    def set_table_data(self,rows,column_names):
            self.tableWidget.setRowCount(len(rows))
            self.tableWidget.setColumnCount(len(rows[0]))
            self.tableWidget.setHorizontalHeaderLabels(column_names)
            self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                        self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))

    def set_date_range(self, min_date, max_date):
            self.dateEdit.setMinimumDate(min_date)
            self.dateEdit.setMaximumDate(max_date)
            self.dateEdit_2.setMinimumDate(min_date)
            self.dateEdit_2.setMaximumDate(max_date)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()