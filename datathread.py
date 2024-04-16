import subprocess
import xmlrpc.client as xc
import time
import datetime
from PySide2 import QtWidgets, QtGui, QtCore

class Signals(QtCore.QObject):
    data = QtCore.Signal(str, str, int, int)
    jid = QtCore.Signal(str)

class DataThread(QtCore.QThread):
    def __init__(self, jid, parent=None):
        super().__init__(parent)
        self.jid = jid
        self.__signals: Signals = Signals()
        self.deadline_command = "C:\\Program Files\\Thinkbox\\Deadline10\\bin\\deadlinecommand.exe"
        self.is_running = True
        self.first_running = True

    def stop(self):
        self.is_running = False

    @property
    def signals(self):
        return self.__signals

    def get_job_details(self, id):
        command = [f'{self.deadline_command}', '-GetJobDetails', f'{id}']
        run_command = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        details = run_command.stdout.decode()
        return details

    def set_job_details(self, id):
        '''
        Job의 디테일을 딕셔너리로 가져온다.
        :param id: job ID
        '''
        output = self.get_job_details(id)
        lines = output.split('\n')

        job_details = {
            'Name': None,
            'Status': None,
            'Errors': None,
            'Task States': {}
        }

        job_section = False
        task_states_section = False

        for line in lines:
            if 'Job' in line:
                job_section = True
            elif job_section:
                if 'Name:' in line:
                    job_details['Name'] = line.split(':')[-1].strip()
                elif 'Status:' in line:
                    job_details['Status'] = line.split(':')[-1].strip()
                elif 'Errors:' in line:
                    job_details['Errors'] = line.split(':')[-1].strip()

            if 'Task States' in line:
                task_states_section = True
                job_section = False
            elif task_states_section:
                if ':' in line:
                    key, value = line.split(':')
                    job_details['Task States'][key.strip()] = value.strip()
                else:
                    task_states_section = False

        return job_details

    def run(self):
        # 스레드가 돌고 있을 때 상태별로 다른 정보를 emit한다.
        while self.is_running:
            try:
                job_details = self.set_job_details(self.jid)
                name = job_details["Name"]
                status = job_details["Status"]
                error = int(job_details["Errors"])
                fail = int(job_details["Task States"]['Failed'])

                if status.startswith("Rendering") and self.first_running:
                    self.signals.data.emit(name, status, error, fail)
                    self.first_running = False

                elif status == "Completed":
                    self.signals.data.emit(name, status, error, fail)
                    self.signals.jid.emit(self.jid)
                    break

                elif error > 0 or fail > 0:
                    self.signals.data.emit(name, status, error, fail)
                    break

            except Exception as err:
                print("an error occurred:", err)

            time.sleep(1)

    def run_start(self):
        self.start()

if __name__ == '__main__':
    pass