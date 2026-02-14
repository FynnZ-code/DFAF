from DFAutomationFramework.ProcessingWrapper import ProcessingWrapper
import time


class DummyWrapper(ProcessingWrapper):
    """
    Worker that accepts dummy Tasks. During a dummy task the worker sends 2 logs and then waits
    for an input to finish the task. Is used for testing purposes.
    """
    def __init__(self, task, worker):
        super().__init__(task, worker)
        return

    def execute(self):
        """
        Sends a log and waits 1 minute. Then sends a Log again and waits until input is received.
        """
        self.pass_through_log("doing dummy things . . . ")
        time.sleep(60)
        self.pass_through_log("still doing dummy things . . . ")
        input("Press Enter to finish dummy process.")
