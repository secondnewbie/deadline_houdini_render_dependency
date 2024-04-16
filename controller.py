
import hou
import pathlib
import xmlrpc.client as xc
import logging
import datetime
import subprocess
import platform
import tempfile
import os

from PySide2 import QtWidgets, QtCore, QtGui

from libraries.qt import library as qt_lib

from view import UIView
from model import TreeModel, TableModel

from datathread import DataThread


class Controller(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.view = UIView()
        self.tree_item = list()
        self.table_item = list()

        self.tree_model = TreeModel()
        self.table_model = TableModel(self.table_item)

        self.view.tree_node.setModel(self.tree_model)
        self.view.table_ren_node.setModel(self.table_model)

        self.view.show()

        self.main_sig()

        self.deadline_command = "C:\\Program Files\\Thinkbox\\Deadline10\\bin\\deadlinecommand.exe"

        self.tmp_check_lst = []
        self.tmp_job_file_list = []
        self.tmp_plugin_file_list = []

        self.__msg = qt_lib.LogHandler(out_stream=self.view.debug_slot)

        self.data_threads = []

    def main_sig(self):
        self.view.tool_btn.clicked.connect(self.open_file)
        self.tree_model.checkStateChanged.connect(self.check_node)
        self.view.push_btn_ren.clicked.connect(self.start_render)
        self.view.push_btn_can.clicked.connect(self.cancel_render)
        self.view.push_btn_clear.clicked.connect(self.tree_clear)

    def slot_open(self):
        """
        렌더할 후디니 파일 오픈
        """
        dir = QtWidgets.QFileDialog.getOpenFileName(self.view, 'Open File', '/data/workspace/houdini/sj')
        if dir[0]:
            fpath = pathlib.Path(dir[0])
            self.view.line_fpath.setText(str(fpath))
            return fpath
        else:
            return None

    @property
    def get_file_path(self) -> pathlib.Path:
        """
        파일 경로를 메서드화한다.
        """
        fpath = self.view.line_fpath.text()
        return pathlib.Path(fpath)

    def open_file(self):
        fpath = self.slot_open()
        if fpath:
            hou.hipFile.load(str(fpath))

            root_node = hou.node('/')
            nodes = self.show_node(root_node)

            self.tree_item.append(nodes)

            self.tree_model.setupModelData(self.tree_item, self.tree_model.rootItem)

            index_1 = self.tree_model.findItem('/')
            self.view.tree_node.expand(index_1)

            index_2 = self.tree_model.findItem('obj', index_1)
            self.view.tree_node.expand(index_2)

            index_3 = self.tree_model.findItem('out', index_1)
            self.view.tree_node.expand(index_3)

    def show_node(self, node, indent = 0):
        """
        자식 노드들 중 'f1'이라는 파라미터를 갖고 있는 노드들만 찾는다.
        :param node: 부모노드
        """
        node_data = {'name': str(node.name()), 'children': []}

        if indent < 7:
            for child in node.children():
                child_data = self.show_node(child, indent + 3)
                node_data['children'].append(child_data)

        return node_data


    @QtCore.Slot(str, bool)
    def check_node(self, nodeName, checked):
        """
        :param nodeName: 시그널의 변경이 있던 노드
        :param checked: 체크 상태(True, False)
        :return:
        """
        # 추가를 위해 체크박스를 클릭했다면, checked == True
        if checked:
            if nodeName not in self.tmp_check_lst:
                self.tmp_check_lst.append(nodeName)

                # table_ren_node의 맨 밑에 새로운 열 추가
                newRow = len(self.table_item)
                self.table_model.beginInsertRows(QtCore.QModelIndex(), newRow, newRow)
                self.table_item.append([newRow + 1, nodeName, None, None])
                self.table_model.endInsertRows()

                # 공백이었던 프레임 시작과 끝 값을 해당 노드에서 가져온다.
                fs_index = self.table_model.index(newRow, 2)
                fe_index = self.table_model.index(newRow, 3)
                fs = self.table_model.data(fs_index, TableModel.FS)
                fe = self.table_model.data(fe_index, TableModel.FE)
                self.table_item[-1][2] = fs
                self.table_item[-1][3] = fe

        # 제거를 위해 체크박스를 클릭했다면, checked == False
        else:
            if nodeName in self.tmp_check_lst:
                self.tmp_check_lst.remove(nodeName)

                # nodeName과 일치하는 열 제거
                for row, item in enumerate(self.table_item):
                    if item[1] == nodeName:
                        self.table_model.beginRemoveRows(QtCore.QModelIndex(), row, row)
                        self.table_item.pop(row)
                        self.table_model.endRemoveRows()

    def make_dependency_dict(self):
        """
        노드별 기입한 우선순위를 기준으로 노드의 종속성을 딕셔너리로 구현한다. (key: priority, value: node이름)
        """
        num_list = []
        ren_dict = {}
        # table_model에 있는 모든 데이터의 우선순위를 num_list에 담는다.
        for i in range(len(self.tmp_check_lst)):
            index = self.table_model.index(i, 0)
            num = self.table_model.data(index, QtCore.Qt.DisplayRole)
            num_list.append(num)

        for id, it in enumerate(num_list):
            # 중복 숫자가 없다면 ren_dict에 담는다.
            if num_list.count(it) == 1:
                index = self.table_model.index(id, 1)
                name = self.table_model.data(index, QtCore.Qt.DisplayRole)
                ren_dict[it] = name

            # 중복 숫자가 있다면 value값인 node이름들을 리스트로 만든 후에 ren_dict에 담는다.
            else:
                ch_list = list(filter(lambda x: num_list[x] == it, range(len(num_list))))
                sm_list = []
                if id == ch_list[0]:
                    for tmp in ch_list:
                        index = self.table_model.index(tmp, 1)
                        name = self.table_model.data(index, QtCore.Qt.DisplayRole)
                        sm_list.append(name)
                    ren_dict[it] = sm_list

        # 우선순위에 맞게 내림차순으로 정렬한다.
        sorted_ren_dict = {k: ren_dict[k] for k in sorted(ren_dict, reverse=True)}

        return sorted_ren_dict

    def find_row_by_name(self, name):
        """
        table_model에서 이름을 활용해 데이터의 row 넘버를 찾는다.
        :param name: 노드 이름
        """
        for row in range(self.table_model.rowCount()):
            index = self.table_model.index(row, 1)
            if self.table_model.data(index, QtCore.Qt.DisplayRole) == name:
                return row
        return -1

    def make_job_info(self, num, node, time):
        res = """Plugin=Houdini
        Name=%s - %s
        BatchName=%s - %s
        Frames=1001-1120
        ChunkSize=200
        """ % (num, node, self.get_file_path.name, time)
        return res

    def make_plugin_info(self, hip_path, node):
        res = """Version=19.5
        SceneFile="%s"
        OutputDriver=/out/%s
        """ % (hip_path, node)
        return res

    def make_tmp_job_file(self, info_file):
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.txt') as tmp_job_file:
            tmp_job_file.write(info_file)
            tmp_job_file.flush()
            self.tmp_job_file_list.append(tmp_job_file)
        return tmp_job_file

    def make_tmp_plugin_file(self, info_file):
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.txt') as tmp_plugin_file:
            tmp_plugin_file.write(info_file)
            tmp_plugin_file.flush()
            self.tmp_plugin_file_list.append(tmp_plugin_file)
        return tmp_plugin_file

    def make_render_dependency(self, data: dict):
        today = datetime.datetime.today()
        for num, node in data.items():
            if not isinstance(node, list):
                job = self.make_job_info(num, node, today)
                plugin = self.make_plugin_info(str(self.get_file_path), node)
                self.make_tmp_job_file(job)
                self.make_tmp_plugin_file(plugin)
            else:
                for i, n in enumerate(node):
                    job = self.make_job_info(f'{num}_{len(node)-i}', n, today)
                    plugin = self.make_plugin_info(str(self.get_file_path), n)
                    self.make_tmp_job_file(job)
                    self.make_tmp_plugin_file(plugin)

    def set_command(self, job_lst, plugin_lst):
        command = [f'{self.deadline_command}', '-SubmitMultipleJobs', '-Dependent']
        for num, job in enumerate(job_lst):
            command.extend(['-Job', f'{job.name}', f'{plugin_lst[num].name}'])
        return command

    def remove_tmp_file(self, lst: list):
        for tmp in lst:
            os.remove(tmp.name)
        lst.clear()

    def get_job_ids(self, res):
        output = res.stdout.decode()
        lines = output.split('\n')
        id_list = []
        for line in lines:
            if 'JobID=' in line:
                job_id = line.split('=')[-1].strip()
                id_list.append(job_id)
        return id_list

    def start_render(self):
        # 렌더 시작 전, 초기화
        self.data_threads.clear()
        self.view.debug_slot.clear()
        self.view.progressbar.setValue(0)

        self.view.debug_slot.setTextColor(QtGui.QColor("Orange"))
        self.view.debug_slot.setText(f'*****{self.get_file_path.name} RENDER START*****')

        final_dict = self.make_dependency_dict()

        # 렌더 시작
        self.make_render_dependency(final_dict)
        command = self.set_command(self.tmp_job_file_list, self.tmp_plugin_file_list)
        res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.job_id_list = self.get_job_ids(res)

        for jid in self.job_id_list:
            data_thread = DataThread(jid)
            self.data_threads.append(data_thread)
            data_thread.signals.data.connect(self.debug_msg)
            data_thread.run_start()

        self.work_data = dict()
        self.get_single_ratio()

        self.remove_tmp_file(self.tmp_job_file_list)
        self.remove_tmp_file(self.tmp_plugin_file_list)

    @QtCore.Slot(str, str, int, int)
    def debug_msg(self, name, status, error, fail):
        """
        job의 현재 상태에 맞게 디버깅창에 메시지를 띄운다.
        :param name: job 이름
        :param status: job 상태
        :param starttime: job 시작 시간
        :param endtime: job 끝난 시간
        """

        status_lst = []

        if status.startswith("Rendering") and status not in status_lst:
            qt_lib.LogHandler.log_msg(logging.info, f'RENDER START : {name}')
            pass

        elif status == "Completed":
            qt_lib.LogHandler.log_msg(logging.debug, f'RENDER SUCCEED : {name}')

        elif error > 0 or fail > 0:
            self.view.debug_slot.setTextColor(QtGui.QColor("Red"))
            qt_lib.LogHandler.log_msg(logging.critical, f'RENDER FAIL : {name}')
            self.fail_render()

        if status not in status_lst:
            status_lst.append(status)
        else:
            pass

    def get_single_ratio(self):
        for thread in self.data_threads:
            thread.signals.jid.connect(self.total_progress)

    @QtCore.Slot(str)
    def total_progress(self, jid):
        self.work_data[jid] = 1
        completed_count = sum(self.work_data.values())
        total_count = len(self.data_threads)
        ratio = (completed_count / total_count) * 100
        self.view.progressbar.setValue(ratio)

        if self.view.progressbar.value() == 100:
            self.view.debug_slot.setTextColor(QtGui.QColor("Blue"))
            self.view.debug_slot.append(f'*****{self.get_file_path.name} RENDER SUCCESS*****')

    def fail_command(self, id_list:list):
        cancel_id_list = ''
        for id in id_list:
            cancel_id_list += f'{id},'

        command = [f'{self.deadline_command}', '-FailJob']
        command.append(cancel_id_list)
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def fail_render(self):
        for thread in self.data_threads:
            if thread.isRunning():
                thread.stop()
                thread.wait()
        self.fail_command(self.job_id_list)
        self.view.debug_slot.setTextColor(QtGui.QColor("Red"))
        self.view.debug_slot.append(f'*****{self.get_file_path.name} RENDER Fail*****')


    def cancel_command(self, id_list:list):
        cancel_id_list = ''
        for id in id_list:
            cancel_id_list += f'{id},'

        command = [f'{self.deadline_command}', '-DeleteJob']
        command.append(cancel_id_list)
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def cancel_render(self):
        for thread in self.data_threads:
            if thread.isRunning():
                thread.stop()
                thread.wait()
        self.cancel_command(self.job_id_list)
        self.view.debug_slot.setTextColor(QtGui.QColor("Red"))
        self.view.debug_slot.append(f'*****{self.get_file_path.name} RENDER CANCEL*****')

    def tree_clear(self):
        """
        트리 뷰에서 모든 체크된 노드를 체크 해제하고 관련 데이터를 테이블에서 제거한다
        """
        self.clear_checked_nodes(self.tree_model.rootItem)

    def clear_checked_nodes(self, parentItem):
        """
        재귀적으로 모든 자식 노드를 순회하며 체크된 노드의 체크를 해제한다.
        :param parentItem: 순회 중인 부모 아이템
        """
        for child in parentItem.childitems:
            if child.checked != QtCore.Qt.Unchecked:
                child.checked = QtCore.Qt.Unchecked
                self.check_node(child.itemdata['name'], False)
                index = self.tree_model.indexFromItem(child)
                self.tree_model.dataChanged.emit(index, index, [QtCore.Qt.CheckStateRole])
            self.clear_checked_nodes(child)

if __name__ == "__main__":
    # pass
    app = QtWidgets.QApplication([])
    ma = Controller()
    app.exec_()

