# - - - - Imports - - - - #
from DFAutomationFramework.ProcessingWrapper import ProcessingWrapper
from DFAutomationFramework.DBWrapper import DBWrapper

import sys
import socket
import threading
import json
import yaml
import time
import argparse
import traceback
import os
from requests import ReadTimeout, JSONDecodeError
from importlib import resources


class Worker:
    def __init__(self, master_host, master_port, managable_tasks):
        self.host = socket.gethostname()
        self.master_host = master_host
        self.master_port = int(master_port)
        self.managable_tasks = managable_tasks.split(',')
        self.db_connection = DBWrapper.create_DBWrapper()
        self.status = 'idle'
        self.log = f'''Worker created with params;
            host: {self.host},
            master_host: {self.master_host},
            master_port: {self.master_port},
            status: {self.status}
        '''
        self.current_task = {'tasks': []}
        self.lock = threading.Lock()
        self.orphan = False
        self.client = None
        return

    def connect_to_master(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.client is not None:
            sockname = self.client.getsockname()
            client.bind(sockname)
        client.connect((self.master_host, self.master_port))
        self.client = client
        return

    def start(self):
        self.connect_to_master()
        master_con = threading.Thread(target=self.report_to_master, args=())
        task_listener = threading.Thread(target=self.listen_for_task, args=())
        master_con.start()
        task_listener.start()
        master_con.join()
        task_listener.join()
        print("shutting down . . . ")

    def report_to_master(self):
        global REPORTTICKRATE
        while True:
            try:
                with self.lock:
                    current_task = ','.join([task['uid'] for task in self.current_task['tasks']])
                    register_message = json.dumps({
                        'type': 'register',
                        'host': self.host,
                        'status': self.status,
                        'log': '(last log) ' + self.log,
                        'managable_tasks': self.managable_tasks,
                        'current_task': current_task if current_task != "" else 'None'
                    })
                    register_message = register_message.encode('utf-8')
                self.client.send(register_message)
                time.sleep(REPORTTICKRATE)
            except ConnectionResetError:
                print("The connection to the master has been closed.")
                if self.status == 'busy':
                    with self.lock:
                        self.orphan = True
                    print("Becoming Orphan Thread (Reporting Loop)")
                    while True:
                        try:
                            print("trying to reconnect to master . . . (Reporting Loop) ")
                            self.connect_to_master()
                            print("succesfully reastablished a connection to the master. (Reporting Loop)")
                            with self.lock:
                                self.orphan = False
                            break
                        except:
                            print(f"failed. trying again in {REPORTTICKRATE}s. (Reporting Loop)")
                            time.sleep(REPORTTICKRATE)
                else:
                    print("Shutting down Listening Loop.")
                    break
            except ConnectionAbortedError:
                print("Connection has been aborted by the Master. Shutting down Reporting Loop.")
                break

    def listen_for_task(self):
        while True:
            try:
                data = self.client.recv(1024).decode('utf-8')
                message = json.loads(data)
                if message['type'] == 'task':
                    if message['task'] in self.managable_tasks:
                        self.report_log(f"Received Task from Master. Task UID: {message['uid']}")
                        execution_thread = threading.Thread(target=self.execute_task, args=(message,))
                        execution_thread.start()
                        if not message['multithread']:
                            execution_thread.join()

                    else:
                        self.report_log(log_msg=f"Can not manage this type of task; task uid {message['uid']}")
                else:
                    time.sleep(10)
            except ConnectionResetError:
                print("The connection to the master has been closed. (Listening Loop)")
                if self.status == 'busy':
                    print("Becoming Orphan Thread (Listening Loop)")
                    while self.status == 'busy':
                        with self.lock:
                            self.orphan = True
                        try:
                            print("trying to reconnect to master . . . (Listening Loop) ")
                            self.connect_to_master()
                            print("succesfully reastablished a connection to the master. (Listening Loop)")
                            with self.lock:
                                self.orphan = False
                            break
                        except Exception as e:
                            print(f"failed Error: {e}. trying again in {REPORTTICKRATE}s. (Listening Loop)")
                            time.sleep(REPORTTICKRATE)
                else:
                    print("Shutting down Listening Loop.")
                    break
            except ConnectionAbortedError:
                print("Connection has been aborted by the Master. Shutting down Listening Loop.")
                break
            except Exception as e:
                self.report_log(log_msg=f'A critical Error occured during listening for tasks: {e}')
                traceback.print_exception(e, limit=None, file=sys.stdout)

    def execute_task(self, task):
        self.status = 'busy'
        self.current_task['tasks'].append(task)
        self.report_log(log_msg=f"Execute Task uid {task['uid']}")
        os.chdir("C:\\")
        try:
            process = ProcessingWrapper.create_process(task, self)
            process.execute()
            if process.successful:
                self.status = 'finished'
            else:
                self.status = 'failed'
            self.report_log(log_msg=f"Finished Task uid {task['uid']}")
        except ReadTimeout as e:
            self.status = 'failed'
            self.report_log(log_msg=f' Task {task['uid']} failed. Connection read timeout during API request: {str(e)}')
            traceback.print_exception(e, limit=None, file=sys.stdout)
        except JSONDecodeError as e:
            self.status = 'failed'
            self.report_log(log_msg=f' Task {task['uid']} failed. API request did not result in a valid response.')
            traceback.print_exception(e, limit=None, file=sys.stdout)
        except Exception as e:
            self.status = 'failed'
            self.report_log(log_msg=f' Task {task['uid']} failed. Uncaught critical error occured during process: ')
            traceback.print_exception(e, limit=None, file=sys.stdout)

        os.chdir("C:\\")

        self.current_task['tasks'] = [task_l for task_l in self.current_task['tasks'] if task_l['uid'] != task['uid']]
        if not self.current_task['tasks']:
            self.status = 'idle'
        self.report_log(log_msg=f"Finished Task uid {task['uid']}. Becoming idle . . .")
        return

    def report_log(self, log_msg=None):
        if log_msg is not None:
            self.log = log_msg

        current_task = ','.join([task['uid'] for task in self.current_task['tasks']])
        msg = json.dumps({
            'type': 'log',
            'host': self.host,
            'status': self.status,
            'log': self.log,
            'current_task': current_task if current_task != "" else 'None'
        })
        print(msg)
        with self.lock:
            if not self.orphan:
                self.client.send(msg.encode('utf-8'))
        time.sleep(2)
        return


# - - - - Entrypoint - - - - #
def main(tasks):
    global REPORTTICKRATE

    parser = argparse.ArgumentParser()
    parser.add_argument('--tasks', required=True, type=str, help="List of managable Tasks seperated by ','")
    module_path = resources.files("DFAutomationFramework")
    specs_file_path = os.path.join(module_path, "configs", "specs.yml")
    with open(specs_file_path, 'r', encoding='utf-8') as specs_file:
        specs = yaml.safe_load(specs_file)
        REPORTTICKRATE = specs['ReportTickRate']
        MASTERHOST = specs['MasterHost']
        CLUSTERPORT = specs['ClusterPort']

    worker = Worker(master_host=MASTERHOST, master_port=CLUSTERPORT, managable_tasks=tasks)
    worker.start()
