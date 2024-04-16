
import hou

from PySide2 import QtWidgets, QtCore, QtGui

class TreeItem:
    def __init__(self, data, parent=None):
        self.parentitem = parent
        self.itemdata = data
        self.childitems = []
        self.checked = QtCore.Qt.Unchecked

    def appendChild(self, item):
        self.childitems.append(item)

    def child(self, row):
        return self.childitems[row]

    def childCount(self):
        return len(self.childitems)

    def columnCount(self):
        return 1

    def data(self, column):
        if column == 0:
            return self.itemdata['name']
        return None

    def setData(self, column, value):
        if column == 0:
            self.checked = value
            return True
        return False

    def parent(self):
        return self.parentitem

    def row(self):
        if self.parentitem:
            return self.parentitem.childitems.index(self)
        return 0


class TreeModel(QtCore.QAbstractItemModel):
    # 클래스 변수
    checkStateChanged = QtCore.Signal(str, bool)

    def __init__(self):
        super().__init__()
        self.rootItem = TreeItem([{'name': '/', 'children': []}])

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            return self.rootItem.childCount()
        else:
            return parent.internalPointer().childCount()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def data(self, index, role=...):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == QtCore.Qt.DisplayRole:
            return item.data(index.column())

        if role == QtCore.Qt.CheckStateRole:
            return item.checked
        return None

    def setData(self, index, value, role=...):
        if role == QtCore.Qt.CheckStateRole:
            item = index.internalPointer()
            item.setData(index.column(), value)
            self.dataChanged.emit(index, index)
            self.checkStateChanged.emit(item.data(0), value == QtCore.Qt.Checked)
            return True
        return False

    def flags(self, index):
        defaultFlags = super(TreeModel, self).flags(index)
        return defaultFlags | QtCore.Qt.ItemIsUserCheckable

    def index(self, row, column, parent=...):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.parent()
        if parentItem == self.rootItem:
            return QtCore.QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def setupModelData(self, data, parentItem):
        self.beginResetModel()
        parentItem.childitems.clear()
        for element in data:
            item = TreeItem({'name': element['name'], 'children': []}, parentItem)
            parentItem.appendChild(item)
            if 'children' in element:
                self._setupModelData(element['children'], item)
        self.endResetModel()

    def _setupModelData(self, data, parentItem):
        for element in data:
            new_item = TreeItem({'name': element['name'], 'children': []}, parentItem)
            parentItem.appendChild(new_item)
            if 'children' in element:
                self._setupModelData(element['children'], new_item)

    def indexFromItem(self, item):
        if item == self.rootItem or not item:
            return QtCore.QModelIndex()
        return self.createIndex(item.row(), 0, item)

    def findItem(self, name, parent=QtCore.QModelIndex()):
        parentItem = self.rootItem if not parent.isValid() else parent.internalPointer()
        for row in range(parentItem.childCount()):
            childItem = parentItem.child(row)
            if childItem.itemdata['name'] == name:
                return self.createIndex(row, 0, childItem)
            else:
                result = self.findItem(name, self.createIndex(row, 0, childItem))
                if result.isValid():
                    return result
        return QtCore.QModelIndex()


class TableModel(QtCore.QAbstractTableModel):
    # 클래스 변수
    FS = QtCore.Qt.UserRole + 1
    FE = QtCore.Qt.UserRole + 2

    def __init__(self, data):
        super().__init__()
        self._data = data
        self.headers = ['PRIOR', 'NODE', 'FSTART', 'FEND']

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.headers)

    def data(self, index, role=...):
        if role == QtCore.Qt.DisplayRole:
            return self._data[index.row()][index.column()]

        # 숫자를 바꿀 수 있는 우선순위만 색깔을 다르게 한다.
        elif role == QtCore.Qt.ForegroundRole:
            if index.column() == 0:
                return QtGui.QBrush(QtGui.QColor(255, 0, 0))

        # 시작프레임 정보 가져오기
        elif role == TableModel.FS:
            if self._data[index.row()][1] is not None:
                node = hou.node(f'/out/{self._data[index.row()][1]}')
                return str(int(node.parm('f1').eval()))

        # 끝프레임 정보 가져오기
        elif role == TableModel.FE:
            if self._data[index.row()][1] is not None:
                node = hou.node(f'/out/{self._data[index.row()][1]}')
                return str(int(node.parm('f2').eval()))

        return None

    def headerData(self, section, orientation, role=...):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.headers[section]
        return None

    def flags(self, index):
        if index.column() == 0:
            return super().flags(index) | QtCore.Qt.ItemIsEditable
        else:
            return super().flags(index)

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            if index.column() == 0:
                try:
                    self._data[index.row()][index.column()] = int(value)
                except ValueError:
                    return False
                self.dataChanged.emit(index, index, [role])
                return True
        return False

if __name__ == '__main__':
    pass

