import sys

from PySide2.QtWidgets import QApplication

from remover.RemoverDialog import RemoverDialog


def main():
    app = QApplication(sys.argv)

    dlg = RemoverDialog()
    dlg.show()

    app.exec_()


if __name__ == '__main__':
    main()
