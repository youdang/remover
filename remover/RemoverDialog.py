import os
import shutil

import PySide2
from PySide2.QtCore import QAbstractTableModel
from PySide2.QtCore import QDir
from PySide2.QtCore import QDirIterator
from PySide2.QtCore import QFile
from PySide2.QtCore import QFileInfo
from PySide2.QtCore import QSortFilterProxyModel
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QAbstractItemView
from PySide2.QtWidgets import QApplication
from PySide2.QtWidgets import QCheckBox
from PySide2.QtWidgets import QDialog
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QHBoxLayout
from PySide2.QtWidgets import QHeaderView
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QLineEdit
from PySide2.QtWidgets import QMenuBar
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import QStyle
from PySide2.QtWidgets import QTableView
from PySide2.QtWidgets import QVBoxLayout
from send2trash import send2trash


def incrementCount(d, key, newItem):
    oldItem = d.get(key)
    if oldItem:
        oldItem.count += newItem.count
    else:
        d[key] = newItem


class ResultItem(object):
    def __init__(self, name, type, count):
        self.name = name
        self.type = type
        self.count = count


class ResultModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super(ResultModel, self).__init__(parent)
        self.rootPath = ''
        self.list = []
        if self.rootPath:
            self.reload(self.rootPath)

    def columnCount(self, parent=None):
        return 2

    def rowCount(self, parent=None):
        return len(self.list)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if section == 0:
                return 'Item'
            else:
                return 'Count'
        return None

    def data(self, index, role=Qt.DisplayRole):
        if index.row() > len(self.list) or index.column() >= 2:
            return None

        if role == Qt.DecorationRole:
            if index.column() != 0:
                return None
            return self.determineIcon(self.list[index.row()])
        if role == Qt.TextAlignmentRole:
            if index.column() == 0:
                return Qt.AlignLeft
            else:
                return Qt.AlignRight
        elif role == Qt.UserRole:
            return self.list[index.row()]
        elif role == Qt.DisplayRole:
            if index.column() == 0:
                return self.list[index.row()].name
            else:
                return self.list[index.row()].count
        else:
            return None

    def reload(self, path):
        self.beginResetModel()
        iterator = QDirIterator(path,
                                filter=QDir.Files | QDir.Dirs | QDir.Hidden | QDir.NoDotAndDotDot,
                                flags=QDirIterator.Subdirectories)
        stats = {}
        while iterator.hasNext():
            file = iterator.next()
            if '.' == file[-1] or '..' == file[-2]:
                continue
            fileInfo = QFileInfo(file)

            if fileInfo.isDir():
                name = fileInfo.fileName()
                key = name + '$d'
                incrementCount(stats, key, ResultItem(name, 'folder', 1))
            else:
                name = fileInfo.fileName()
                key = name + '$f'
                incrementCount(stats, key, ResultItem(name, 'file', 1))
                if fileInfo.suffix():
                    name = '*.' + fileInfo.suffix()
                    key = name + '$s'
                    incrementCount(stats, key, ResultItem(name, 'suffix', 1))

        self.list = list(stats.values())
        self.endResetModel()

    def determineIcon(self, item):
        if 'folder' == item.type:
            return QApplication.style().standardIcon(QStyle.SP_DirIcon)
        elif 'file' == item.type:
            return QApplication.style().standardIcon(QStyle.SP_FileIcon)
        else:
            return None


class SortFilterResultModel(QSortFilterProxyModel):
    def __init__(self, source, parent=None):
        super(SortFilterResultModel, self).__init__(parent)
        self.setSourceModel(source)

    def lessThan(self, left, right):
        model = self.sourceModel()
        l, r = model.data(left, Qt.UserRole), model.data(right, Qt.UserRole)
        if left.column() == 1:
            if l.count != r.count:
                return l.count < r.count
        lv, rv = l.name, r.name
        if l.type == 'suffix':
            lv = lv[2:]
        if r.type == 'suffix':
            rv = rv[2:]
        return lv < rv

    def filterAcceptsRow(self, row, parent):
        model = self.sourceModel()
        index = model.index(row, 0, parent)
        d = model.data(index, Qt.UserRole)
        return self.filterRegularExpression().match(d.type).hasMatch()


class RemoverDialog(QDialog):
    def __init__(self, parent=None):
        super(RemoverDialog, self).__init__(parent)

        self.setupUi()

    def setupUi(self):
        self.menuBar = QMenuBar()
        self.menuBar.show()

        self.pathInputBox = QLineEdit(self)
        self.pathInputBox.setEnabled(False)
        self.pathInputBox.setToolTip('Input a path or drag a directory here...')

        self.openPathButton = QPushButton('Open...', self)
        self.openPathButton.clicked.connect(self.openPath)

        inputLayout = QHBoxLayout()
        inputLayout.addWidget(QLabel('Path:', self))
        inputLayout.addWidget(self.pathInputBox)
        inputLayout.addWidget(self.openPathButton)

        self.filterFolderCheckBox = QCheckBox('Folders', self)
        self.filterFolderCheckBox.setChecked(True)
        self.filterFolderCheckBox.toggled.connect(self.filter)
        self.filterFileCheckBox = QCheckBox('Files', self)
        self.filterFileCheckBox.setChecked(True)
        self.filterFileCheckBox.toggled.connect(self.filter)
        self.filterSuffixCheckBox = QCheckBox('Suffixes', self)
        self.filterSuffixCheckBox.setChecked(True)
        self.filterSuffixCheckBox.toggled.connect(self.filter)

        filterLayout = QHBoxLayout()
        filterLayout.addWidget(self.filterFolderCheckBox)
        filterLayout.addWidget(self.filterFileCheckBox)
        filterLayout.addWidget(self.filterSuffixCheckBox)
        filterLayout.addStretch()

        self.trashButton = QPushButton('Trash', self)
        self.trashButton.clicked.connect(self.trash)
        self.deleteButton = QPushButton('Delete', self)
        self.deleteButton.clicked.connect(self.delete)

        confirmLayout = QHBoxLayout()
        confirmLayout.addStretch()
        confirmLayout.addWidget(self.trashButton)
        confirmLayout.addWidget(self.deleteButton)

        layout = QVBoxLayout()
        layout.addLayout(inputLayout)
        layout.addLayout(filterLayout)
        layout.addWidget(self.createResultView())
        layout.addLayout(confirmLayout)

        self.setAcceptDrops(True)
        self.setLayout(layout)
        self.setMinimumWidth(600)
        self.setWindowTitle('Remover')
        self.setWindowIcon(QApplication.style().standardIcon(QStyle.SP_DirIcon))

    def createResultView(self):
        self.resultModel = ResultModel(self)
        self.resultView = QTableView(self)
        self.resultView.setSortingEnabled(True)
        self.resultView.setShowGrid(False)
        self.resultView.setAlternatingRowColors(True)
        self.resultView.verticalHeader().hide()
        self.resultView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.resultView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.sortFilterModel = SortFilterResultModel(self.resultModel, self)
        self.resultView.setModel(self.sortFilterModel)
        return self.resultView

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) == 1:
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) == 1:
            self.pathInputBox.setText(event.mimeData().urls()[0].toLocalFile())
            self.reloadPath(self.pathInputBox.text())

    def openPath(self):
        path = QFileDialog.getExistingDirectory(parent=self,
                                                caption='Open',
                                                options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if path:
            self.pathInputBox.setText(path)
            self.reloadPath(path)

    def filter(self):
        filters = []
        if self.filterFolderCheckBox.isChecked():
            filters.append('folder')
        if self.filterFileCheckBox.isChecked():
            filters.append('file')
        if self.filterSuffixCheckBox.isChecked():
            filters.append('suffix')
        self.sortFilterModel.setFilterRegularExpression('|'.join(filters))
        self.sortFilterModel.filterRegularExpression()
        self.resultView.resizeRowsToContents()

    def trash(self):
        folders, files = self.collectSelectedFolderFiles()

        try:
            for file in files:
                send2trash(file)
            for folder in folders:
                if QFile(folder).exists():
                    send2trash(folder)
        except:
            QMessageBox.warning(self, 'Failed', 'Failed to trash selected files/folders')
            return

        self.reloadPath(self.pathInputBox.text())

    def delete(self):
        folders, files = self.collectSelectedFolderFiles()

        try:
            for file in files:
                os.remove(file)
            for folder in folders:
                shutil.rmtree(folder)
        except:
            QMessageBox.warning(self, 'Failed', 'Failed to delete selected files/folders')
            return

        self.reloadPath(self.pathInputBox.text())

    def collectSelectedFolderFiles(self):
        folders, files, suffixes = [], [], []
        for index in self.resultView.selectedIndexes():
            if index.column() != 0:
                # 忽略第二列的selection
                continue
            item = self.sortFilterModel.data(index, Qt.UserRole)
            if 'folder' == item.type:
                folders.append(item.name)
            elif 'file' == item.type:
                files.append(item.name)
            elif 'suffix' == item.type:
                suffixes.append(item.name[2:])

        # 将后缀符合选中条件的文件添加到files中
        path = self.pathInputBox.text()
        iterator = QDirIterator(path,
                                filter=QDir.Files | QDir.Dirs | QDir.Hidden | QDir.NoDotAndDotDot,
                                flags=QDirIterator.Subdirectories)
        folderPaths, filePaths = set(), set()
        while iterator.hasNext():
            file = iterator.next()
            if '.' == file[-1] or '..' == file[-2]:
                continue
            fileInfo = QFileInfo(file)
            if fileInfo.isDir():
                if fileInfo.fileName() in folders:
                    folderPaths.add(fileInfo.absoluteFilePath())
            if fileInfo.isFile():
                if fileInfo.fileName() in files:
                    filePaths.add(fileInfo.absoluteFilePath())
                if fileInfo.suffix() in suffixes:
                    filePaths.add(fileInfo.absoluteFilePath())
        return sorted(folderPaths), filePaths

    def reloadPath(self, path):
        self.resultModel.reload(path)
        self.resultView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.resultView.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.filter()
        self.resultView.sortByColumn(1, Qt.DescendingOrder)
