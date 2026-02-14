from importlib import resources
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pathlib import Path
import socket
import threading
import json
import yaml
import time
import datetime
import logging
import sys
import os
import traceback

global MASTERHOST
global UIPORT
global CLUSTERPORT
global REPORTTICKRATE
global TASKQUEUETICKRATE


# - - - - Master DB - - - -  #
class MasterDB:
    def __init__(self):
        # Sets the path to the log file
        data_path = os.path.join(resources.files("DFAutomationFramework"), "data")
        if not os.path.exists(data_path):
            Path.mkdir(data_path)
        self.master_db_path = os.path.join(data_path, "MasterDB.json")

        # Init JSON
        self.clients = {}
        data = {'workers': [], 'tasks': []}
        if not os.path.exists(self.master_db_path):
            with open(self.master_db_path, 'w', encoding='utf-8') as db_file:
                json.dump(data, db_file, indent=4, ensure_ascii=False)

        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data_last_session = json.load(db_file)
        # Add open Tasks to task queue form the last session if there are still tasks in the db
        if 'tasks' in list(data_last_session.keys()):
            if len(data_last_session['tasks']) > 0:
                open_tasks_last_session = [
                    task
                    for task
                    in data_last_session['tasks']
                    if task['status'] == 'open' or task['status'] == 'running'
                ]
                data["tasks"] = open_tasks_last_session
        with open(self.master_db_path, 'w', encoding='utf-8') as db_file:
            json.dump(data, db_file, indent=4, ensure_ascii=False)

    def get_workers(self, filter_keys=None, filter_values=None):
        """
        Returns a list of all active shares.
        With the status argument one can ask for active shares with a specific status.
        """
        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)
        workers = data['workers']

        if filter_keys is not None and filter_values is not None:
            workers_filtered = []
            filter_keys_sep = filter_keys.split(',')
            filter_values_sep = filter_values.split(',')
            if len(filter_keys_sep) != len(filter_values_sep):
                raise Exception("Number of fitler values has to be equal to the number of filter keys")
            for worker in workers:
                filter_flag = True
                for i in range(len(filter_keys_sep)):
                    filter_flag = filter_flag and worker[filter_keys_sep[i]] == filter_values_sep[i]
                if filter_flag:
                    workers_filtered.append(worker)
            workers = workers_filtered

        for worker in workers:
            worker['client'] = self.clients[f"{worker['ip']},{worker['port']}"]
        return workers

    def add_worker(self, worker):
        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)

        self.clients[f"{worker['ip']},{worker['port']}"] = worker['client']
        keys_without_client = set([key for key in list(worker.keys()) if key != 'client'])
        worker = {k: worker[k] for k in keys_without_client}
        data['workers'].append(worker)
        with open(self.master_db_path, 'w', encoding='utf-8') as db_file:
            json.dump(data, db_file, indent=4, ensure_ascii=False)

    def remove_worker(self, host, port):
        """ Removes the entry with the given id."""
        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)
        filtered_workers = [obj for obj in data['workers'] if not (obj['host'] == host and obj['port'] == port)]
        data['workers'] = filtered_workers
        with open(self.master_db_path, 'w', encoding='utf-8') as db_file:
            json.dump(data, db_file, indent=4, ensure_ascii=False)

    def set_worker_value(self, host, port, key, value):
        """  Sets the status of the share given to the status given."""
        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)
        for worker in data['workers']:
            if worker['host'] == host and port in worker['port']:
                worker[key] = value
        with open(self.master_db_path, 'w', encoding='utf-8') as db_file:
            json.dump(data, db_file, indent=4, ensure_ascii=False)

    def set_worker(self, host, port, worker):
        """  Sets the status of the share given to the status given. """
        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)
        for worker_iter in data['workers']:
            if worker_iter['host'] == host and port in worker_iter['port']:
                worker_iter = worker
        with open(self.master_db_path, 'w', encoding='utf-8') as db_file:
            json.dump(data, db_file, indent=4, ensure_ascii=False)

    def get_task(self, filter_keys=None, filter_values=None):
        """
        Returns a list of all active shares.
        With the status argument one can ask for active shares with a specific status.
        """
        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)
        tasks = data['tasks']

        if filter_keys is not None and filter_values is not None:
            tasks_filtered = []
            filter_keys_sep = filter_keys.split(',')
            filter_values_sep = filter_values.split(',')
            if len(filter_keys_sep) != len(filter_values_sep):
                raise Exception("Number of fitler values has to be equal to the number of filter keys")
            for task in tasks:
                filter_flag = True
                for i in range(len(filter_keys_sep)):
                    filter_flag = filter_flag and task[filter_keys_sep[i]] == filter_values_sep[i]
                if filter_flag:
                    tasks_filtered.append(task)
            tasks = tasks_filtered
        return tasks

    def add_task(self, task):
        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)
        data['tasks'].append(task)
        with open(self.master_db_path, 'w', encoding='utf-8') as db_file:
            json.dump(data, db_file, indent=4, ensure_ascii=False)

    def remove_task(self, id):
        """  Removes the entry with the given id. """
        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)
        filtered_tasks = [obj for obj in data['tasks'] if obj['uid'] != str(id)]
        data['tasks'] = filtered_tasks
        with open(self.master_db_path, 'w', encoding='utf-8') as db_file:
            json.dump(data, db_file, indent=4, ensure_ascii=False)

    def set_task_value(self, id, key, value):
        """  Sets the status of the share given to the status given. """
        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)
        for task in data['tasks']:
            if task['uid'] == str(id):
                task[key] = value
        with open(self.master_db_path, 'w', encoding='utf-8') as db_file:
            json.dump(data, db_file, indent=4, ensure_ascii=False)

    def set_task(self, id, task):
        """ Sets the status of the share given to the status given. """
        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)
        for task_iter in data['tasks']:
            if task_iter['id'] == id:
                task_iter = task  # Funktioniert das?
        with open(self.master_db_path, 'w', encoding='utf-8') as db_file:
            json.dump(data, db_file, indent=4, ensure_ascii=False)

    def exists_task(self, id):
        """ Check if share with given id already exists """
        id_exists = False
        with open(self.master_db_path, 'r', encoding='utf-8') as db_file:
            data = json.load(db_file)
        if len([task for task in data['tasks'] if task['id'] == id]) > 0:
            id_exists = True
        return id_exists


# - - - - Master Worker - - - - #
class MasterWorker:
    def __init__(self):
        global MASTERHOST
        global CLUSTERPORT
        self.host = MASTERHOST
        self.port = CLUSTERPORT
        self.lock = threading.Lock()
        self.masterdb = MasterDB()

    def start_server(self):
        self.log_master(f'Server is startet on host {self.host} and port {self.port}')
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)

        listen_for_workers = threading.Thread(target=self.listen_for_workers, args=[server])
        process_task = threading.Thread(target=self.process_task_queue)
        listen_for_workers.start()
        process_task.start()
        listen_for_workers.join()
        process_task.join()

    def listen_for_workers(self, server):
        self.log_master('Listening for Workers')
        while True:
            try:
                worker, addr = server.accept()
                worker_thread = threading.Thread(target=self.handle_worker, args=(worker, addr))
                worker_thread.start()
            except Exception as e:
                logging.warning(f'Critical Error in listen_for_workers Loop: {e}')
                traceback.print_exception(e, limit=None, file=sys.stdout)

    def handle_worker(self, client, addr):
        self.log_master(f'Connecting to Worker on adress {addr}')
        timeout_status = True
        client.settimeout(120)
        while timeout_status:
            try:
                data = client.recv(1024).decode('utf-8')
                message = json.loads(data)
                match message['type']:
                    case 'register':
                        with self.lock:
                            reporting_worker_lst = self.masterdb.get_workers(
                                filter_keys='ip,port',
                                filter_values=f"{addr[0]},{addr[1]}"
                            )
                            if len(reporting_worker_lst) == 0:
                                self.masterdb.add_worker({
                                    'status': message['status'],
                                    'host': message['host'],
                                    'ip': addr[0],
                                    'port': str(addr[1]),
                                    'log': message['log'],
                                    'managable_tasks': message['managable_tasks'],
                                    'client': client,
                                    'current_task': message['current_task'],
                                    'timeout': None,
                                    'kill': False
                                    })
                                reporting_worker_lst = self.masterdb.get_workers(
                                    filter_keys='ip,port',
                                    filter_values=f"{addr[0]},{addr[1]}"
                                )
                                reporting_worker = reporting_worker_lst[0]
                            else:
                                reporting_worker = reporting_worker_lst[0]
                                # Skip logging if status and log has not changed since last log
                                status_matches = reporting_worker['status'] == message['status']
                                log_matches = reporting_worker['log'] == message['log']
                                if status_matches and log_matches:
                                    timeout_status = self.determine_timeout(reporting_worker, message)
                                    continue

                    case 'log':
                        # Processes tasks if the worker reports a finishing or failing of a task
                        if message['status'] == 'finished' or message['status'] == 'failed':
                            with self.lock:
                                corresponding_task = self.masterdb.get_task(
                                    filter_keys="uid",
                                    filter_values=message['current_task']
                                )[0]
                                self.masterdb.set_task_value(corresponding_task['uid'], 'status', message['status'])

                                corresponding_worker = self.masterdb.get_workers(
                                    filter_keys='current_task',
                                    filter_values=message['current_task']
                                )[0]
                                self.masterdb.set_worker_value(
                                    corresponding_worker['host'],
                                    corresponding_worker['port'],
                                    'current_task',
                                    'None'
                                )

                # Determine if Worker is timed out
                timeout_status = self.determine_timeout(reporting_worker, message)
                self.log(addr, message)

            except Exception as e:
                logging.warning(f'''A critical error occured during the handling of worker with address: {addr}.
                                    Exception Message: {e}''')
                traceback.print_exception(e, limit=None, file=sys.stdout)
                timeout_status = False

        self.log_master(f'Shuting down worker on host {reporting_worker['host']}.')
        client.shutdown(socket.SHUT_RDWR)
        client.close()
        self.masterdb.remove_worker(reporting_worker['host'], reporting_worker['port'])
        self.log_master(f'Worker on Host {reporting_worker['host']} has succesfully been shut down.')

    def determine_timeout(self, worker, message):
        timed_out = False
        if worker['timeout'] is not None:
            timeout_timestamp = datetime.datetime.strptime(worker['timeout'], '%Y-%m-%dT%H:%M')
            now = datetime.datetime.now()

            after_timeout = now > timeout_timestamp
            not_busy = message['status'] != 'busy'
            timed_out = after_timeout and not_busy

        kill = bool(worker['kill'])
        timeout_status = not (kill or timed_out)
        return timeout_status

    def process_task_queue(self):  # TODO Adjust to Task_ID in Module Register
        global TASKQUEUETICKRATE
        while True:
            try:
                with self.lock:
                    idle_workers = self.masterdb.get_workers(filter_keys='status', filter_values='idle')

                    open_tasks = []
                    running_tasks = []
                    for process in module_register["processes"]:
                        open_tasks_filtered = self.masterdb.get_task(
                            filter_keys='status,task',
                            filter_values=f'open,{process["name"]}'
                        )
                        running_tasks_filtered = self.masterdb.get_task(
                            filter_keys='status,task',
                            filter_values=f'running,{process["name"]}'
                        )
                        for rule in process["rules"]:
                            open_tasks_filtered, running_tasks_filtered = self.process_ruleset(
                                open_tasks_filtered,
                                running_tasks_filtered,
                                rule
                            )
                        open_tasks += open_tasks_filtered
                        running_tasks += running_tasks_filtered

                if open_tasks and idle_workers:
                    for task in open_tasks:
                        for worker in idle_workers:
                            client_match = True
                            if 'client' in list(task.keys()):
                                client_match = task['client'] == worker['client']
                            if task['task'] in worker['managable_tasks'] and client_match:
                                self.assign_task(worker, task)
                                break
                        else:
                            continue
                        break
                time.sleep(TASKQUEUETICKRATE)
            except Exception as e:
                logging.warning(f'Critical Error during processing of the Task queue: {e}')
                traceback.print_exception(e, limit=None, file=sys.stdout)

    def process_ruleset(self, open_tasks, running_tasks, rule):
        """
        Evaluates a defined task rule. A Rule is defined in the module_register for a process.
        Currently implemented rule types:
            - unambiguous
                Ensures that one value of a given task parameter is unique in running Tasks.
                Example: The Parameter is a case number. The rule ensures, that only 1
                         process from the same case is running at a time.
        """
        match rule["type"]:
            case "unambiguous":
                id_scheme_values = get_default_scheme()
                params = [p["key"] for p in rule["params"]]
                for open_t in open_tasks:
                    for running_t in running_tasks:
                        id_stack = []
                        for val in id_scheme_values["values"]:
                            if val["key"] in params:
                                id_stack.append(open_t[val["key"]] == running_t[val["key"]])

                        if id_stack and all(id_stack):
                            match rule["act"]:
                                case "skip":
                                    open_tasks = [task for task in open_tasks if task['uid'] != open_t['uid']]
                                case "remove":
                                    self.log_master(f'''Amiguous Task found.
                                                      Deleting Task {open_t['uid']} from Task Queue''')
                                    open_tasks = [task for task in open_tasks if task['uid'] != open_t['uid']]
                                    self.masterdb.remove_task(open_t['uid'])
        return open_tasks, running_tasks

    def assign_task(self, worker, task):
        """
        Assigns the given task to the given worker.
            - Task is send to the Worker as json payload.
            - Task status is set to running.
        """
        client = worker['client']
        task_payload = json.dumps(task).encode('utf-8')
        client.send(task_payload)
        with self.lock:
            self.masterdb.set_task_value(task['uid'], 'status', 'running')
        self.log_master(f"Assigned Task with uid {task['uid']} to worker on host {worker['host']}")

    def scedule_task(self, task):
        """
        Adds the given task to the task queue.
        """
        with self.lock:
            self.masterdb.add_task(task)
        self.log_master(f'Added Task to Queue: {str(task)}')
        return

    def log(self, addr, msg):
        """
        Formats the given Log Message and passes it to the active Logger. Use for received Worker Logs.
        """
        with self.lock:
            worker = self.masterdb.get_workers(filter_keys='ip,port', filter_values=f"{addr[0]},{addr[1]}")[0]
            self.masterdb.set_worker_value(worker['host'], worker['port'], 'status', msg['status'])
            self.masterdb.set_worker_value(worker['host'], worker['port'], 'log', msg['log'])
            self.masterdb.set_worker_value(worker['host'], worker['port'], 'current_task', msg['current_task'])

        failed = msg['status'] == "failed"
        exception = "exception" in msg['log'].lower()
        if failed or exception:
            logging.warning(f"{msg['host']}:{addr[1]} :: {msg['status']} :: {msg['log']}")
        else:
            logging.info(f"{msg['host']}:{addr[1]} :: {msg['status']} :: {msg['log']}")
        return

    def log_master(self, msg):
        """
        Formats the given Log Message and passes it to the active Logger. Used for logging by the Master itself.
        """
        logging.info(f'$ Master :: {msg}')


# - - - - Globals - - - - #
module_path = resources.files("DFAutomationFramework")
config_folder = os.path.join(module_path, "configs")
config_folder_exists = os.path.exists(config_folder)
if not config_folder_exists:
    os.mkdir(config_folder)

specs_file_path = os.path.join(config_folder, "specs.yml")
specs_file_exists = os.path.exists(specs_file_path)
if not specs_file_exists:
    default_config = {
        "MasterHost": "localhost",
        "UIPort": 5000,
        "ClusterPort": 6531,
        "ReportTickRate": 10,
        "TaskQueueTickRate": 5
    }
    with open(specs_file_path, 'w', encoding='utf-8') as config_file:
        yaml.dump(default_config, config_file, default_flow_style=False)

with open(specs_file_path, 'r', encoding='utf-8') as specs_file:
    specs = yaml.safe_load(specs_file)

    MASTERHOST = specs['MasterHost']
    UIPORT = specs['UIPort']
    CLUSTERPORT = specs['ClusterPort']
    REPORTTICKRATE = specs['ReportTickRate']
    TASKQUEUETICKRATE = specs['TaskQueueTickRate']

module_register_path = os.path.join(config_folder, "module_register.yml")
with open(module_register_path, 'r', encoding='utf-8') as module_register_file:
    module_register = yaml.safe_load(module_register_file)

app = Flask(__name__)
master = MasterWorker()


# - - - - Functions - - - - #
def get_logs(limit=None):
    with open(os.path.join(resources.files("DFAutomationFramework"), "logs", "Master.log"), "r") as master_log:
        lines = master_log.readlines()

    i = 0
    last_occurence = None
    for line in lines:
        if "Server is startet on " in line:
            last_occurence = i
        i += 1
    current_log = lines[last_occurence:]
    current_log = list(reversed(current_log))
    current_log = [log for log in current_log if 'OpenSSH' not in log and ' Authentication ' not in log]

    logs_formatted = format_logs(current_log, reverse=False)
    if limit is not None:
        logs_formatted = logs_formatted[:limit]
    return logs_formatted


def get_task_info(task_id):
    task = None
    worker = {
            "port": "",
            "managable_tasks": [
            ],
            "log": "",
            "ip": "",
            "kill": False,
            "timeout": None,
            "host": "",
            "status": "",
            "current_task": ""
        }
    logs_formatted = []
    task = master.masterdb.get_task(filter_keys="uid", filter_values=str(task_id))[0]

    module_path = resources.files("DFAutomationFramework")
    logging_path = os.path.join(module_path, "logs", "Master.log")
    with open(logging_path, "r") as master_log:
        lines = master_log.readlines()
    current_log = lines
    worker_id = None
    logs = []
    for log in current_log:
        if task_id in log:
            logs.append(log)
            if 'Execute Task' in log:
                worker_id = log.split('|')[2].split('::')[0].strip()
            if 'Finished Task' in log:
                break
        elif worker_id is not None and worker_id in log:
            logs.append(log)

    logs_formatted = format_logs(logs)

    if worker_id is not None:
        host = worker_id.split(':')[0]
        port = worker_id.split(':')[1]
        filter_values = f"{host},{port}"
        worker_lst = master.masterdb.get_workers(filter_keys="host,port", filter_values=filter_values)
        if len(worker_lst) == 1:
            worker = worker_lst[0]
    return task, logs_formatted, worker


def get_worker_info(host, port):  # TODO Adjust to Task_ID in module Register
    task = None
    worker = None
    logs_formatted = []

    worker = master.masterdb.get_workers(
        filter_keys="host,port",
        filter_values=",".join([host, port]))[0]

    module_path = resources.files("DFAutomationFramework")
    logging_path = os.path.join(module_path, "logs", "Master.log")
    with open(logging_path, "r") as master_log:
        lines = master_log.readlines()
    current_log = lines
    worker_id = ':'.join([worker['host'], worker['port']])
    logs = []
    for log in current_log:
        if worker_id in log:
            logs.append(log)
    logs_formatted = format_logs(logs)

    if worker['current_task'] is not None:
        task_lst = master.masterdb.get_task(
            filter_keys="uid",
            filter_values=str(worker['current_task'])
        )
        if len(task_lst) == 1:
            task = task_lst[0]
    else:
        task = {
            "type": "task",
            "uid": "",
            "task": "",
            "status": "",
            "multithread": False
        }
        task_id_default_scheme = get_default_scheme()
        for val in task_id_default_scheme["values"]:
            task[val["key"]] = ""
    return task, logs_formatted, worker


def format_logs(logs, reverse=True):
    logs_formatted = []
    for log in logs:
        try:
            entry = {
                    "type": log.split("|")[0].strip(),
                    "timestamp": log.split("|")[1].strip()
                }
            content_array = log.split("|")[2].strip().split(" :: ")
        except:  # TODO Write proper Except clause
            entry["type"] = "WARNING"
            entry["timestamp"] = "-"
            entry["worker"] = "Unknown"
            entry["status"] = "-"
            entry["text"] = log
        if "$ Master" in log:
            entry["worker"] = "Master"
            entry["status"] = "-"
            entry["text"] = content_array[1]
        elif len(content_array) == 3:
            entry["worker"] = content_array[0]
            entry["status"] = content_array[1]
            entry["text"] = content_array[2]
        else:
            entry["worker"] = "Unknown"
            entry["status"] = "-"
            entry["text"] = "".join(content_array)
        logs_formatted.append(entry)
    if reverse:
        logs_formatted = list(reversed(logs_formatted))
    return logs_formatted


def get_default_scheme():
    return [scheme for scheme in module_register["dbwrapper"]["TaskID"] if scheme["default"]][0]


def run_flask():
    global MASTERHOST
    global UIPORT
    app.run(host=MASTERHOST, port=UIPORT, debug=False)


# - - - - Flask App - - - - #
# -------------------
#       Dashboard
# -------------------
@app.route("/", methods=["GET", "POST"])
def dashboard():
    workers = master.masterdb.get_workers()
    tasks = master.masterdb.get_task()
    logs = get_logs(limit=100)
    task_id_default_scheme = get_default_scheme()
    return render_template(
        "Dashboard.html",
        workers=workers,
        tasks=tasks,
        logs=logs,
        task_id_scheme=task_id_default_scheme["values"]
    )


# -------------------
#       Tasks
# -------------------
@app.route("/tasks", methods=['GET'])
def tasks():
    tasks = master.masterdb.get_task()
    task_id_default_scheme = get_default_scheme()
    return render_template(
        "tasks.html",
        tasks=tasks,
        task_id_scheme=task_id_default_scheme["values"]
    )


@app.route("/tasks/<task_id>", methods=['GET'])
def taskview(task_id):
    if request.method == 'GET':
        try:
            task, logs, worker = get_task_info(task_id)
        except Exception as e:  # TODO Write propper Except clause
            traceback.print_exception(e, limit=None, file=sys.stdout)
            return redirect(url_for("tasks"))
        task_id_default_scheme = get_default_scheme()
    return render_template(
        "taskview.html",
        task=task,
        logs=logs,
        worker=worker,
        task_id_scheme=task_id_default_scheme["values"]
    )


@app.route("/tasks/<task_id>/delete", methods=['GET'])
def deletetask(task_id):
    with master.lock:
        master.masterdb.remove_task(task_id)
    return redirect(url_for("tasks"))


@app.route("/tasks/create", methods=['GET', 'POST'])
def tasks_create():
    if request.method == "POST":  # TODO zerlegen von Tasks mit mehreren Asservaten in einzelne Aufgaben
        multithreadable_tasks = ('FTK')
        multithread = False
        task = {
            'type': 'task',
            'status': 'open',
            'multithread': multithread
        }

        # TODO API for creating Tasks. Read either from form or json payload/url_params
        task_id_default_scheme = get_default_scheme()
        for val in task_id_default_scheme["values"]:
            task[val["key"]] = request.form.get(val["key"]).replace(' ', '').strip()
        task["task"] = request.form.get('task').strip()
        if task["task"] in multithreadable_tasks:
            task["multithread"] = True

        task_uid_tmp = str(datetime.datetime.now()) + task["task"]
        for val in task_id_default_scheme["values"]:
            task_uid_tmp += str(task[val["key"]])
        task_uid = str(hash(task_uid_tmp))
        task['uid'] = task_uid

        match task["task"]:
            case "FTK":
                drive_nr = request.form.get('drive_nr')
                client = request.form.get('client')
                task['drive_nr'] = drive_nr
                task['client'] = client

        master.scedule_task(task)
        return redirect(url_for("tasks"))

    elif request.method == "GET":
        processes = module_register["processes"]
        task_id_default_scheme = get_default_scheme()
        return render_template(
            "taskCreate.html",
            processes=processes,
            task_id_scheme=task_id_default_scheme["values"]
        )


# -------------------
#       Workers
# -------------------
@app.route("/workers", methods=['GET'])
def workers():
    workers = master.masterdb.get_workers()
    return render_template("workers.html", workers=workers)


@app.route("/workers/<host>/<port>", methods=['GET'])
def workerview(host, port):
    try:
        task, logs, worker = get_worker_info(host, port)
    except Exception as e:  # TODO Write propper exception clause
        traceback.print_exception(e, limit=None, file=sys.stdout)
        return redirect(url_for("workers"))
    return render_template(
        "workerview.html",
        worker=worker,
        task=task,
        logs=logs
    )


@app.route("/workers/<host>/<port>/timeout", methods=['GET', 'POST'])
def workertimeout(host, port):
    if request.method == "POST":
        enable_kill = request.form.get('enableKill') is not None
        if enable_kill:
            with master.lock:
                master.masterdb.set_worker_value(host, port, 'kill', True)
        else:
            timeout_str = request.form.get('timestamp').strip()
            with master.lock:
                master.masterdb.set_worker_value(host, port, 'timeout', timeout_str)

        return redirect(url_for("workers"))

    worker = master.masterdb.get_workers(
        filter_keys="host,port",
        filter_values=','.join([host, port])
    )[0]
    return render_template("workerKill.html", worker=worker)


# -------------------
#       Master
# -------------------
@app.route("/master", methods=["GET", "POST"])
def masterview():
    workers = master.masterdb.get_workers()
    tasks = master.masterdb.get_task()
    logs = get_logs()
    stated_at = [log["timestamp"] for log in logs if "Server is startet on host " in log['text']][0]
    config = {
        "MasterHost": MASTERHOST,
        "UIPort": UIPORT,
        "ClusterPort": CLUSTERPORT,
        "ReportTickRate": REPORTTICKRATE,
        "TaskQueueTickRate": TASKQUEUETICKRATE,
        "StartedAt": stated_at
    }

    metrics = {
        "ActiveWorkers": len(workers),
        "Tasks": len(tasks),
        "Logs": len(logs),
        # TODO can be solved better - define a function and just pass open ect. at the function here.
        "OpenTasks": len(list(filter(lambda x: x["status"] == "open", tasks))),
        "RunningTasks": len(list(filter(lambda x: x["status"] == "running", tasks))),
        "FinishedTasks": len(list(filter(lambda x: x["status"] == "finished", tasks))),
        "FailedTasks": len(list(filter(lambda x: x["status"] == "failed", tasks))),
    }
    return render_template("masterView.html", metrics=metrics, logs=logs, config=config)


# -------------------
#       Utility
# -------------------
@app.route("/update", methods=["GET"])
def update():
    workers = []
    with master.lock:
        for worker in master.masterdb.get_workers():
            workers.append({k: worker[k] for k in ('host', 'status', 'current_task', 'managable_tasks', 'log', 'port')})
        tasks = master.masterdb.get_task()

        task_id_default_scheme = get_default_scheme()
    return jsonify({
        "workers": workers,
        "tasks": tasks,
        "logs": get_logs(limit=100),
        "task_id_scheme": task_id_default_scheme["values"]
    })


# - - - - Entrypoint - - - - #
def main(thirdparty_logging):
    log_folder_path = os.path.join(module_path, "logs")
    if not os.path.exists(log_folder_path):
        os.mkdir(log_folder_path)
    logging_path = os.path.join(log_folder_path, "Master.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(asctime)s | %(message)s",
        filename=logging_path,
        filemode="a",
        encoding="utf-8",
    )
    logging.getLogger(__name__).addHandler(logging.StreamHandler(sys.stdout))

    if not thirdparty_logging:
        # Set thirdparty logging to only log warnings
        flask_logger = logging.getLogger('werkzeug')
        flask_logger.setLevel(logging.WARNING)
        app.logger.disabled = True
        flask_logger.disabled = True
        ssh_logger = logging.getLogger('sshtunnel')
        ssh_logger.setLevel(logging.WARNING)
        ssh_logger.disabled = True

    threading.Thread(target=master.start_server, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()
    input()
