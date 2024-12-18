from random import random

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QProgressBar, QVBoxLayout,QTableWidgetItem, QLabel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from ui.Ui_Table import Ui_Table
from ui.Ui_Form import Ui_Form
from ui.Ui_Login import Ui_Login


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

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class CategoriesView(QtWidgets.QWidget):
    def __init__(self, formLayout, verticalLayout):
        super(CategoriesView, self).__init__()
        self.formLayout = formLayout
        self.verticalLayout = verticalLayout

    def color_generation(self):
        r = lambda: random.randint(0, 255)
        colors = '#%02X%02X%02X' % (r(), r(), r())
        return colors

    def update_progress_bars(self, df_categories):
        colors = []
        for col_name, data in df_categories.items():
            color = self.color_generation()
            colors.append(color)
            pbar = QProgressBar()
            pbar.setRange(0, int(df_categories.max()))
            pbar.setStyleSheet(f"QProgressBar::chunk {{background-color: {color} }}")
            pbar.setValue(int(data))
            pbar.setFormat(f'{int(data)}')
            pbar.setAlignment(Qt.AlignRight)
            self.formLayout.addRow(col_name, pbar)
        return colors


    def update_chart(self, df_categories, colors):
        sc = MplCanvas(self, width=5, height=4, dpi=100)
        data = [float(i) for i in df_categories.tolist()]
        ax = df_categories.plot(ax=sc.axes)
        ax.pie(data, colors=colors, wedgeprops={"edgecolor": "black", 'linewidth': 1, 'antialiased': True})
        self.verticalLayout.addWidget(sc)

    def show_no_data_message(self):
        self.label = QLabel("Нет данных")
        self.label.setAlignment(Qt.AlignCenter)
        self.formLayout.addRow(self.label)
