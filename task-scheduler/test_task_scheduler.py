import threading
import time

import pytest
from task_scheduler import Task, Scheduler


def make_started_scheduler():
    s = Scheduler()
    s.start()
    return s


# ---------- schedule_once validation ----------

def test_schedule_once_empty_name_raises():
    s = Scheduler()

    with pytest.raises(ValueError):
        s.schedule_once("", lambda: None)


def test_schedule_once_whitespace_name_raises():
    s = Scheduler()

    with pytest.raises(ValueError):
        s.schedule_once("   ", lambda: None)


def test_schedule_once_non_callable_raises():
    s = Scheduler()

    with pytest.raises(TypeError):
        s.schedule_once("job", "not a function")  # type: ignore


def test_schedule_once_negative_delay_raises():
    s = Scheduler()

    with pytest.raises(ValueError):
        s.schedule_once("job", lambda: None, delay=-1)


# ---------- schedule_recurring validation ----------

def test_schedule_recurring_zero_interval_raises():
    s = Scheduler()

    with pytest.raises(ValueError):
        s.schedule_recurring("job", lambda: None, interval=0)


def test_schedule_recurring_negative_interval_raises():
    s = Scheduler()

    with pytest.raises(ValueError):
        s.schedule_recurring("job", lambda: None, interval=-1)


def test_schedule_recurring_negative_delay_raises():
    s = Scheduler()

    with pytest.raises(ValueError):
        s.schedule_recurring("job", lambda: None, interval=1, delay=-1)


# ---------- scheduling bookkeeping (scheduler not started) ----------

def test_schedule_once_returns_id_and_stores_task():
    s = Scheduler()

    task_id = s.schedule_once("job", lambda: None, delay=10)

    assert task_id is not None
    assert task_id in s.tasks
    assert s.tasks[task_id].name == "job"
    assert s.tasks[task_id].interval is None
    assert len(s.heap) == 1


def test_schedule_recurring_stores_interval():
    s = Scheduler()

    task_id = s.schedule_recurring("job", lambda: None, interval=5, delay=10)

    assert s.tasks[task_id].interval == 5
    assert len(s.heap) == 1


def test_schedule_returns_unique_ids():
    s = Scheduler()

    id1 = s.schedule_once("a", lambda: None, delay=10)
    id2 = s.schedule_once("b", lambda: None, delay=10)

    assert id1 != id2
    assert len(s.tasks) == 2


def test_heap_top_is_earliest_task():
    s = Scheduler()

    s.schedule_once("late", lambda: None, delay=10)
    early_id = s.schedule_once("early", lambda: None, delay=1)

    assert s.heap[0][2] == early_id


def test_counter_increments_per_schedule():
    s = Scheduler()

    s.schedule_once("a", lambda: None, delay=10)
    s.schedule_once("b", lambda: None, delay=10)

    assert s.counter == 2


# ---------- cancel ----------

def test_cancel_existing_task_returns_true():
    s = Scheduler()
    task_id = s.schedule_once("job", lambda: None, delay=10)

    assert s.cancel(task_id) is True
    assert task_id not in s.tasks


def test_cancel_unknown_task_returns_false():
    s = Scheduler()

    assert s.cancel("no-such-task") is False


def test_cancel_twice_second_returns_false():
    s = Scheduler()
    task_id = s.schedule_once("job", lambda: None, delay=10)

    assert s.cancel(task_id) is True
    assert s.cancel(task_id) is False


def test_cancel_is_lazy_heap_entry_remains():
    s = Scheduler()
    task_id = s.schedule_once("job", lambda: None, delay=10)

    s.cancel(task_id)

    assert len(s.heap) == 1  # stale entry is skipped later by the loop, not removed now


def test_cancelled_task_never_runs():
    s = make_started_scheduler()
    ran = threading.Event()

    task_id = s.schedule_once("job", ran.set, delay=0.2)
    s.cancel(task_id)

    assert not ran.wait(timeout=0.5)
    s.stop()


# ---------- start / stop ----------

def test_start_sets_running_and_thread():
    s = Scheduler()

    s.start()

    assert s.running is True
    assert s.thread is not None
    assert s.thread.is_alive()
    s.stop()


def test_start_twice_keeps_single_thread():
    s = Scheduler()

    s.start()
    first_thread = s.thread
    s.start()

    assert s.thread is first_thread
    s.stop()


def test_stop_ends_thread():
    s = make_started_scheduler()

    s.stop()

    assert s.running is False
    assert not s.thread.is_alive()


def test_stop_without_start_does_not_crash():
    s = Scheduler()

    s.stop()

    assert s.running is False


def test_stop_wakes_loop_that_is_waiting_on_far_future_task():
    s = make_started_scheduler()
    s.schedule_once("far", lambda: None, delay=60)
    time.sleep(0.05)  # let the loop go to sleep on the 60s wait

    start = time.time()
    s.stop()

    assert time.time() - start < 1  # did not wait the full 60s


# ---------- execution: one-shot ----------

def test_schedule_once_runs_the_function():
    s = make_started_scheduler()
    ran = threading.Event()

    s.schedule_once("job", ran.set, delay=0.05)

    assert ran.wait(timeout=2)
    s.stop()


def test_schedule_once_does_not_run_before_delay():
    s = make_started_scheduler()
    ran = threading.Event()

    s.schedule_once("job", ran.set, delay=0.5)

    assert not ran.wait(timeout=0.2)  # still too early
    assert ran.wait(timeout=2)        # but it does run eventually
    s.stop()


def test_schedule_once_runs_only_once():
    s = make_started_scheduler()
    calls = []

    s.schedule_once("job", lambda: calls.append(1), delay=0.05)
    time.sleep(0.4)

    assert len(calls) == 1
    s.stop()


def test_schedule_once_task_removed_after_running():
    s = make_started_scheduler()
    ran = threading.Event()

    task_id = s.schedule_once("job", ran.set, delay=0.05)
    assert ran.wait(timeout=2)
    time.sleep(0.1)

    assert task_id not in s.tasks
    s.stop()


def test_tasks_run_in_order_of_run_at():
    s = make_started_scheduler()
    order = []
    done = threading.Event()

    def record(label):
        order.append(label)
        if len(order) == 3:
            done.set()

    s.schedule_once("third", lambda: record("C"), delay=0.4)
    s.schedule_once("first", lambda: record("A"), delay=0.1)
    s.schedule_once("second", lambda: record("B"), delay=0.25)

    assert done.wait(timeout=3)
    assert order == ["A", "B", "C"]
    s.stop()


def test_earlier_task_added_later_wakes_the_loop():
    """Loop is sleeping on a 10s task. A new 0.1s task must wake it up
    and run on time instead of waiting behind the 10s one."""
    s = make_started_scheduler()
    s.schedule_once("far", lambda: None, delay=10)
    time.sleep(0.05)  # loop is now waiting for the far task

    ran = threading.Event()
    s.schedule_once("soon", ran.set, delay=0.1)

    assert ran.wait(timeout=2)
    s.stop()


# ---------- execution: recurring ----------

def test_recurring_task_runs_multiple_times():
    s = make_started_scheduler()
    calls = []

    s.schedule_recurring("tick", lambda: calls.append(1), interval=0.05)
    time.sleep(0.5)

    assert len(calls) >= 3
    s.stop()


def test_recurring_task_stays_registered():
    s = make_started_scheduler()

    task_id = s.schedule_recurring("tick", lambda: None, interval=0.05)
    time.sleep(0.3)

    assert task_id in s.tasks
    s.stop()


def test_cancel_recurring_task_stops_future_runs():
    s = make_started_scheduler()
    calls = []

    task_id = s.schedule_recurring("tick", lambda: calls.append(1), interval=0.05)
    time.sleep(0.3)
    s.cancel(task_id)
    time.sleep(0.1)                 # let any in-flight run finish
    count_after_cancel = len(calls)

    time.sleep(0.3)

    assert len(calls) == count_after_cancel
    s.stop()


def test_recurring_task_respects_initial_delay():
    s = make_started_scheduler()
    ran = threading.Event()

    s.schedule_recurring("tick", ran.set, interval=0.05, delay=0.4)

    assert not ran.wait(timeout=0.2)
    assert ran.wait(timeout=2)
    s.stop()


# ---------- failure handling ----------

def test_failing_task_does_not_kill_scheduler():
    s = make_started_scheduler()
    ran = threading.Event()

    def bad():
        raise RuntimeError("boom")

    s.schedule_once("bad", bad, delay=0.05)
    s.schedule_once("good", ran.set, delay=0.2)

    assert ran.wait(timeout=2)
    assert s.thread.is_alive()
    s.stop()


def test_failing_task_error_is_printed(capsys):
    s = make_started_scheduler()
    done = threading.Event()

    def bad():
        try:
            raise RuntimeError("boom")
        finally:
            done.set()

    s.schedule_once("bad-job", bad, delay=0.05)
    assert done.wait(timeout=2)
    time.sleep(0.1)

    out = capsys.readouterr().out
    assert "bad-job" in out
    assert "boom" in out
    s.stop()


# ---------- slow tasks must not block the scheduler ----------

def test_slow_task_does_not_block_other_tasks():
    s = make_started_scheduler()
    fast_ran = threading.Event()

    s.schedule_once("slow", lambda: time.sleep(1), delay=0)
    s.schedule_once("fast", fast_ran.set, delay=0.1)

    assert fast_ran.wait(timeout=0.6)  # well before the slow task finishes
    s.stop()


def test_slow_task_does_not_block_schedule_calls():
    s = make_started_scheduler()
    s.schedule_once("slow", lambda: time.sleep(1), delay=0)
    time.sleep(0.1)  # slow task is now running

    start = time.time()
    s.schedule_once("another", lambda: None, delay=5)

    assert time.time() - start < 0.3  # scheduler lock is free during execution
    s.stop()


# ---------- Task ----------

def test_task_defaults():
    task = Task("job", lambda: None, run_at=123.0)

    assert task.id is not None
    assert task.name == "job"
    assert task.interval is None
    assert task.cancelled is False


# ---------- Concurrency ----------

def test_concurrent_schedule_no_lost_tasks():
    """Many threads schedule at the same time. Every task must be stored
    exactly once and the heap counter must not skip or collide."""
    s = Scheduler()
    ids = []
    ids_lock = threading.Lock()

    def attempt(i):
        task_id = s.schedule_once(f"job-{i}", lambda: None, delay=10)
        with ids_lock:
            ids.append(task_id)

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(set(ids)) == 50
    assert len(s.tasks) == 50
    assert len(s.heap) == 50
    assert s.counter == 50


def test_concurrent_schedule_all_tasks_run():
    s = make_started_scheduler()
    calls = []
    calls_lock = threading.Lock()
    all_done = threading.Event()

    def work():
        with calls_lock:
            calls.append(1)
            if len(calls) == 30:
                all_done.set()

    def attempt():
        s.schedule_once("job", work, delay=0.05)

    threads = [threading.Thread(target=attempt) for _ in range(30)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all_done.wait(timeout=3)
    assert len(calls) == 30
    s.stop()


def test_concurrent_cancel_same_task_only_one_wins():
    """Two threads race to cancel the SAME task. Exactly one should get True."""
    s = Scheduler()
    task_id = s.schedule_once("job", lambda: None, delay=10)

    results = {}

    def attempt(name):
        results[name] = s.cancel(task_id)

    t1 = threading.Thread(target=attempt, args=("A",))
    t2 = threading.Thread(target=attempt, args=("B",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert sorted(results.values()) == [False, True]
