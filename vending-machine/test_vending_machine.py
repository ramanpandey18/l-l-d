import threading

import pytest
from vending_machine import Item, SlotStock, Inventory, Machine


# ---------- Inventory.add_item ----------

def test_add_item_success():
    inv = Inventory()
    item = Item("Coke", 1.00)

    item_id = inv.add_item(item)

    assert item_id is not None
    assert item.id == item_id
    assert len(inv.items) == 1
    assert inv.items[0] is item


def test_add_item_empty_name_raises():
    inv = Inventory()
    item = Item("", 1.00)

    with pytest.raises(ValueError):
        inv.add_item(item)


def test_add_item_zero_price_raises():
    inv = Inventory()
    item = Item("Coke", 0.0)

    with pytest.raises(ValueError):
        inv.add_item(item)


def test_add_item_negative_price_raises():
    inv = Inventory()
    item = Item("Coke", -5.0)

    with pytest.raises(ValueError):
        inv.add_item(item)


def test_add_item_non_numeric_price_raises():
    inv = Inventory()
    item = Item("Coke", "free")  # type: ignore

    with pytest.raises(ValueError):
        inv.add_item(item)


def test_add_item_duplicate_name_case_insensitive_raises():
    inv = Inventory()
    inv.add_item(Item("Coke", 1.00))

    with pytest.raises(ValueError):
        inv.add_item(Item("COKE", 1.50))


# ---------- Inventory.assign_slot ----------

def test_assign_slot_success():
    inv = Inventory()
    item_id = inv.add_item(Item("Coke", 1.00))

    inv.assign_slot("A1", item_id, 5)

    assert "A1" in inv.slots
    assert inv.slots["A1"].item.name == "Coke"
    assert inv.slots["A1"].quantity == 5


def test_assign_slot_already_used_raises():
    inv = Inventory()
    item_id = inv.add_item(Item("Coke", 1.00))
    inv.assign_slot("A1", item_id, 5)

    with pytest.raises(ValueError):
        inv.assign_slot("A1", item_id, 3)


def test_assign_slot_unknown_item_id_raises():
    inv = Inventory()

    with pytest.raises(ValueError):
        inv.assign_slot("A1", "no-such-item-id", 5)


def test_assign_slot_zero_quantity_raises():
    inv = Inventory()
    item_id = inv.add_item(Item("Coke", 1.00))

    with pytest.raises(ValueError):
        inv.assign_slot("A1", item_id, 0)


def test_assign_slot_negative_quantity_raises():
    inv = Inventory()
    item_id = inv.add_item(Item("Coke", 1.00))

    with pytest.raises(ValueError):
        inv.assign_slot("A1", item_id, -1)


def test_assign_slot_empty_slot_code_raises():
    inv = Inventory()
    item_id = inv.add_item(Item("Coke", 1.00))

    with pytest.raises(ValueError):
        inv.assign_slot("", item_id, 5)


# ---------- Inventory.restock_slot ----------

def test_restock_slot_increases_quantity():
    inv = Inventory()
    item_id = inv.add_item(Item("Coke", 1.00))
    inv.assign_slot("A1", item_id, 5)

    inv.restock_slot("A1", 10)

    assert inv.slots["A1"].quantity == 15


def test_restock_slot_unknown_slot_raises():
    inv = Inventory()

    with pytest.raises(ValueError):
        inv.restock_slot("A1", 10)


def test_restock_slot_invalid_quantity_raises():
    inv = Inventory()
    item_id = inv.add_item(Item("Coke", 1.00))
    inv.assign_slot("A1", item_id, 5)

    with pytest.raises(ValueError):
        inv.restock_slot("A1", 0)


# ---------- Machine.insert_money ----------

def test_insert_money_valid_denomination():
    m = Machine()

    m.insert_money(1)

    assert m.current_transaction == [1]


def test_insert_money_invalid_denomination_raises():
    m = Machine()

    with pytest.raises(ValueError):
        m.insert_money(3)


def test_insert_money_accumulates_across_multiple_inserts():
    m = Machine()

    m.insert_money(1)
    m.insert_money(1)
    m.insert_money(0.25)

    assert m._get_inserted_total() == 2.25


# ---------- Machine._calculate_change ----------

def test_calculate_change_exact_breakdown():
    m = Machine()
    m.change_reserve = {10: 2, 5: 3, 1: 8, 0.25: 15}

    result = m._calculate_change(1.25)

    assert result == {1: 1, 0.25: 1}


def test_calculate_change_impossible_returns_none():
    m = Machine()
    m.change_reserve = {10: 2, 5: 3, 1: 8, 0.25: 0}  # no quarters

    result = m._calculate_change(0.75)

    assert result is None


def test_calculate_change_zero_owed_returns_empty_dict():
    m = Machine()
    m.change_reserve = {10: 2, 5: 3, 1: 8, 0.25: 15}

    result = m._calculate_change(0.0)

    assert result == {}


# ---------- Machine.select_item ----------

def _make_machine_with_item(price: float, quantity: int, slot_code: str = "A1") -> Machine:
    m = Machine()
    m.change_reserve = {10: 5, 5: 5, 1: 20, 0.25: 20}
    item_id = m.inventory.add_item(Item("Coke", price))
    m.inventory.assign_slot(slot_code, item_id, quantity)
    return m


def test_select_item_exact_payment_success():
    m = _make_machine_with_item(price=1.00, quantity=5)
    m.insert_money(1)

    item, change = m.select_item("A1")

    assert item.name == "Coke"
    assert change == {}
    assert m.inventory.slots["A1"].quantity == 4
    assert m.current_transaction == []


def test_select_item_overpayment_gives_correct_change():
    m = _make_machine_with_item(price=1.00, quantity=5)
    m.insert_money(5)  # $4 change owed

    item, change = m.select_item("A1")

    assert item.name == "Coke"
    assert change == {1: 4}
    assert m.inventory.slots["A1"].quantity == 4
    assert m.current_transaction == []
    # reserve should reflect: -4 ones given as change, +1 five-dollar bill added
    assert m.change_reserve[1] == 20 - 4
    assert m.change_reserve[5] == 5 + 1


def test_select_item_insufficient_funds_raises_and_does_not_refund():
    m = _make_machine_with_item(price=2.00, quantity=5)
    m.insert_money(1)  # not enough yet

    with pytest.raises(ValueError):
        m.select_item("A1")

    # money should still be sitting in the transaction, not refunded/cleared
    assert m.current_transaction == [1]


def test_select_item_sold_out_raises():
    m = _make_machine_with_item(price=1.00, quantity=1)
    m.inventory.slots["A1"].quantity = 0  # simulate the last one already sold
    m.insert_money(1)

    with pytest.raises(ValueError):
        m.select_item("A1")


def test_select_item_nonexistent_slot_raises():
    m = _make_machine_with_item(price=1.00, quantity=5)
    m.insert_money(1)

    with pytest.raises(ValueError):
        m.select_item("Z9")


def test_select_item_cannot_make_change_refuses_and_refunds():
    m = _make_machine_with_item(price=1.00, quantity=5)
    m.change_reserve = {10: 0, 5: 0, 1: 0, 0.25: 0}  # no change available at all
    m.insert_money(5)  # would need $4 change back, but reserve is empty

    with pytest.raises(ValueError):
        m.select_item("A1")

    # transaction should have been refunded/cleared, and stock untouched
    assert m.current_transaction == []
    assert m.inventory.slots["A1"].quantity == 5


# ---------- Machine.cancel_transaction ----------

def test_cancel_transaction_returns_inserted_money_and_clears():
    m = Machine()
    m.insert_money(1)
    m.insert_money(0.25)

    refunded = m.cancel_transaction()

    assert refunded == [1, 0.25]
    assert m.current_transaction == []


# ---------- Concurrency ----------

def test_concurrent_purchase_only_one_winner_for_last_item():
    m = _make_machine_with_item(price=1.00, quantity=1)  # only ONE left

    results = {}

    def attempt(name):
        try:
            local_machine = m
            local_machine.insert_money(1)
            local_machine.select_item("A1")
            results[name] = "SUCCESS"
        except ValueError:
            results[name] = "FAILED"

    t1 = threading.Thread(target=attempt, args=("A",))
    t2 = threading.Thread(target=attempt, args=("B",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    success_count = sum(1 for v in results.values() if v == "SUCCESS")
    assert success_count == 1
    assert m.inventory.slots["A1"].quantity == 0


def test_concurrent_purchase_consistent_across_many_runs():
    for _ in range(20):
        m = _make_machine_with_item(price=1.00, quantity=1)

        results = {}

        def attempt(name, target_machine=m):
            try:
                target_machine.insert_money(1)
                target_machine.select_item("A1")
                results[name] = "SUCCESS"
            except ValueError:
                results[name] = "FAILED"

        t1 = threading.Thread(target=attempt, args=("A",))
        t2 = threading.Thread(target=attempt, args=("B",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        success_count = sum(1 for v in results.values() if v == "SUCCESS")
        assert success_count == 1
