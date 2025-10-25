import os
import importlib
import yaml
from importlib import resources


class DBWrapper:
    module_register_path = os.path.join(resources.files("DFAutomationFramework"), "configs", "module_register.yml")
    def __init__(self):
        return
    
    def get_info(self, Task_ID, params=None):
        return

    def push_note(self, Task_ID, params=None):
        return
    
    def push_info(self, Task_ID, params=None):
        return
    
    @classmethod
    def create_DBWrapper(cls):
        db_connection = None
        with open(cls.module_register_path) as module_register_path:
            module_register = yaml.safe_load(module_register_path)
        dbwrapper_module_entry = module_register["dbwrapper"] 
        if not dbwrapper_module_entry["module"]: # TODO implement a propper handling - should be fixed when a default db is implemented
            return None 
        dbwrapper_module = importlib.import_module(dbwrapper_module_entry["module"])
        dbwrapper_cls = getattr(dbwrapper_module, dbwrapper_module_entry["class"])
        db_connection = dbwrapper_cls()
        return db_connection