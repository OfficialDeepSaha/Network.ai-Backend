import asyncio
from concurrent.futures import ThreadPoolExecutor

class TaskManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)

    def add_task(self, task_fn, *args):
        """Schedules a task to run in the background."""
        loop = asyncio.get_event_loop()
        loop.run_in_executor(self.executor, task_fn, *args)
