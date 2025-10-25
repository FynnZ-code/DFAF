# - - - - Imports - - - - #
import os
import yaml
import importlib
from importlib import resources

class ProcessingWrapper:
    processes_cfg_path = os.path.join(resources.files("DFAutomationFramework"), "configs", "module_register.yml")

    def __init__(self, task, worker, params=None):
        self.task = task
        self.worker = worker
        self.params = params
        self.successful = True
        return 

    def execute(self):

        return
    
    def pass_through_log(self, log_msg):
        self.worker.report_log(log_msg)
        return
    
    @classmethod
    def create_process(cls, task, worker):
        process = None        
        with open(cls.processes_cfg_path) as process_cfg_file:
            processes = yaml.safe_load(process_cfg_file) # TODO Check cfg file vor validity
        for process in processes["processes"]: 
            if process["name"] == task['task']:
                module = importlib.import_module(process["module"])
                process_cls = getattr(module, process["class"])
                process_wrapper = process_cls(task, worker)
                return process_wrapper 
