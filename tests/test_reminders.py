import datetime as dt
import pytest

from src.data.reminders import ReminderStore


def test_reminder_store_schedule_and_due():
    store = ReminderStore()
    base = dt.datetime.now()
    store.schedule(base - dt.timedelta(minutes=5), "Past reminder")
    store.schedule(base + dt.timedelta(minutes=5), "Future reminder")

    due = store.due(reference=base)
    assert len(due) == 1
    assert due[0].message == "Past reminder"

    # Mark triggered and ensure it's no longer in due list
    store.mark_triggered(due[0].id)
    due_after = store.due(reference=base)
    assert len(due_after) == 0


def test_reminder_store_multiple_due_and_order():
    store = ReminderStore()
    now = dt.datetime.now()
    r1 = store.schedule(now - dt.timedelta(minutes=10), "First")
    r2 = store.schedule(now - dt.timedelta(minutes=5), "Second")
    r3 = store.schedule(now + dt.timedelta(minutes=1), "Third future")

    due = store.due(reference=now)
    assert [r.message for r in due] == ["First", "Second"]
    # Ensure order is by when ascending
    assert due[0].when <= due[1].when

    # Mark one and confirm the other remains
    store.mark_triggered(r1.id)
    remaining = store.due(reference=now)
    assert [r.message for r in remaining] == ["Second"]
