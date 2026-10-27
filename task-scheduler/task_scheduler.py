from typing import Optional, Dict, Callable
import threading
import heapq
import time
import uuid


class Task:
    def __init__(self, name: str, func: Callable, run_at: float, interval: Optional[float] = None):
        self.id: str = str(uuid.uuid4())
        self.name = name
        self.func = func
        self.run_at = run_at          # epoch seconds of next run
        self.interval = interval      # None means run once
        self.cancelled = False


class Scheduler:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}      # task_id -> Task
        self.running = False
        self.heap = []                        # (run_at, seq, task_id)
        self.counter: int = 0                 # tie-breaker for the heap
        self.cond = threading.Condition()     # lock + wait/notify in one
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        with self.cond:
            if self.running:
                return
            self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        with self.cond:
            self.running = False
            self.cond.notify_all()
        if self.thread:
            self.thread.join()

    def _validate(self, name, func) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("task name is empty or invalid.")
        if not callable(func):
            raise TypeError("func must be callable.")

    def _push(self, task: Task) -> None:
        # caller must hold self.cond
        self.counter += 1
        heapq.heappush(self.heap, (task.run_at, self.counter, task.id))
        self.cond.notify()                    # wake loop, new task may be earliest

    def schedule_once(self, name, func, delay: float = 0) -> str:
        self._validate(name, func)
        if delay < 0:
            raise ValueError("delay cannot be negative.")
        task = Task(name, func, time.time() + delay)
        with self.cond:
            self.tasks[task.id] = task
            self._push(task)
        return task.id

    def schedule_recurring(self, name, func, interval: float, delay: float = 0) -> str:
        self._validate(name, func)
        if interval <= 0:
            raise ValueError("interval must be positive.")
        if delay < 0:
            raise ValueError("delay cannot be negative.")
        task = Task(name, func, time.time() + delay, interval)
        with self.cond:
            self.tasks[task.id] = task
            self._push(task)
        return task.id

    def cancel(self, task_id: str) -> bool:
        with self.cond:
            task = self.tasks.pop(task_id, None)
            if task is None:
                return False
            task.cancelled = True             # heap entry is skipped lazily
            return True

    def _run_loop(self) -> None:
        while True:
            with self.cond:
                while self.running and not self.heap:
                    self.cond.wait()
                if not self.running:
                    return

                run_at, _, task_id = self.heap[0]
                task = self.tasks.get(task_id)

                if task is None or task.cancelled:
                    heapq.heappop(self.heap)  # drop stale entry
                    continue

                wait_time = run_at - time.time()
                if wait_time > 0:
                    self.cond.wait(wait_time) # sleeps, but wakes on new task or stop
                    continue

                heapq.heappop(self.heap)
                if task.interval is not None:
                    task.run_at = run_at + task.interval
                    self._push(task)
                else:
                    del self.tasks[task_id]

            # run outside the lock so a slow task never blocks scheduling
            threading.Thread(target=self._execute, args=(task,), daemon=True).start()

    def _execute(self, task: Task) -> None:
        try:
            task.func()
        except Exception as e:
            print(f"Task {task.name} failed: {e}")


s = Scheduler()
s.start()

s.schedule_once("hello", lambda: print("hello after 1s"), delay=1)
job = s.schedule_recurring("heartbeat", lambda: print("tick"), interval=0.5)

time.sleep(2.2)
s.cancel(job)
time.sleep(1)
s.stop()
