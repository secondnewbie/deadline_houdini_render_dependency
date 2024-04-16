from PySide2 import QtWidgets, QtCore

class UIView(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__(parent=None)
        self.set_window()

    def set_window(self):
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Render Dependency')

        # open file
        self.line_fpath = QtWidgets.QLineEdit()
        self.line_fpath.setReadOnly(True)
        self.tool_btn = QtWidgets.QToolButton()
        self.tool_btn.setText('Open File')

        # node label
        label_node = QtWidgets.QLabel()
        label_node.setText('Choose Node')

        # open node
        self.tree_node = QtWidgets.QTreeView()
        self.tree_node.header().hide()

        # render node
        self.table_ren_node = QtWidgets.QTableView()
        self.table_ren_node.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table_ren_node.verticalHeader().hide()

        # render btn
        self.push_btn_ren = QtWidgets.QPushButton()
        self.push_btn_ren.setText('Render')

        # render cancel btn
        self.push_btn_can = QtWidgets.QPushButton()
        self.push_btn_can.setText('Cancel')

        # tree widget clear btn
        self.push_btn_clear = QtWidgets.QPushButton()
        self.push_btn_clear.setText('Clear')

        # debug view
        self.debug_slot = QtWidgets.QTextEdit()

        # progress bar
        self.progressbar = QtWidgets.QProgressBar()
        self.progressbar.setValue(0)

        # 레이아웃 설정1 : render
        hlayout_1 = QtWidgets.QHBoxLayout()
        hlayout_2 = QtWidgets.QHBoxLayout()
        hlayout_3 = QtWidgets.QHBoxLayout()
        hlayout_4 = QtWidgets.QHBoxLayout()
        hlayout_5 = QtWidgets.QHBoxLayout()
        hlayout_6 = QtWidgets.QHBoxLayout()
        vlayout_1 = QtWidgets.QVBoxLayout()
        vlayout_2 = QtWidgets.QVBoxLayout()
        vlayout_3 = QtWidgets.QVBoxLayout()
        vlayout_4 = QtWidgets.QVBoxLayout()

        hlayout_1.addWidget(self.line_fpath)
        hlayout_1.addWidget(self.tool_btn)
        vlayout_1.addLayout(hlayout_1)
        vlayout_1.addWidget(label_node)
        vlayout_1.addWidget(self.tree_node)

        hlayout_2.addWidget(self.push_btn_ren)
        hlayout_2.addWidget(self.push_btn_can)
        hlayout_2.addWidget(self.push_btn_clear)
        vlayout_2.addWidget(self.table_ren_node)
        vlayout_2.addLayout(hlayout_2)

        vlayout_3.addWidget(self.debug_slot)
        vlayout_3.addWidget(self.progressbar)

        # splitter 추가
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # splitter로 분단 구분
        widget1 = QtWidgets.QWidget()
        widget1.setLayout(vlayout_1)
        widget1.setMinimumSize(200, 100)
        splitter.addWidget(widget1)

        widget2 = QtWidgets.QWidget()
        widget2.setLayout(vlayout_2)
        widget2.setMinimumSize(250, 100)
        splitter.addWidget(widget2)

        widget3 = QtWidgets.QWidget()
        widget3.setLayout(vlayout_3)
        widget3.setMinimumSize(300, 100)
        splitter.addWidget(widget3)

        hlayout_3.addWidget(splitter)

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(hlayout_3)
        self.setCentralWidget(central_widget)

    def closeEvent(self, event):
        """
        GUI가 종료돼도, 백그라운드에서 작업이 계속 진행된다.
        """
        super().closeEvent(event)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    ui = UIView()
    ui.show()
    app.exec_()


