from PyQt5 import QtWidgets
from model import AccountModel
from view import Ui_Login, LoginView
from controler import LoginController
import sys


def main():
    app = QtWidgets.QApplication(sys.argv)
    model = AccountModel()
    view = LoginView()
    controller = LoginController(model, view)
    view.show()
    sys.exit(app.exec_())

import traceback


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)

    text += ''.join(traceback.format_tb(tb))

    QtWidgets.QMessageBox.critical(None, 'Error', text)

    sys.exit()


sys.excepthook = log_uncaught_exceptions
if __name__ == "__main__":
    main()

