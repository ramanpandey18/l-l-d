from typing import List, Optional, Dict
import threading
import uuid
import math


class Item:
    def __init__(self, name: str, price: float):
        self.id: Optional[str] = None
        self.name = name
        self.price = price


class SlotStock:
    def __init__(self):
        self.item: Optional[Item] = None
        self.quantity: int = 0


class ItemNotFoundError(ValueError):
    pass


class Inventory:
    def __init__(self):
        self.slots: Dict[str, SlotStock] = {}
        self.items: List[Item] = []

    def add_item(self, item: Item) -> str:
        if not isinstance(item.name, str) or item.name.strip() == "":
            raise ValueError("Item name is not correct.")
        if not isinstance(item.price, (int, float)) or item.price <= 0.0 or not math.isfinite(item.price):
            raise ValueError("Item price is not correct.")
        if any(existing.name.lower() == item.name.strip().lower() for existing in self.items):
            raise ValueError(f"Item name '{item.name}' is already registered.")

        item.id = str(uuid.uuid4())
        item.name = item.name.strip()
        self.items.append(item)
        return item.id

    def _find_item(self, item_id: str) -> Item:
        for item in self.items:
            if item.id == item_id:
                return item
        raise ItemNotFoundError(f"No item with the id {item_id}")

    def assign_slot(self, slot_code: str, item_id: str, quantity: int):
        if slot_code.strip() == "":
            raise ValueError("Slot code is empty")
        if quantity <= 0:
            raise ValueError(f"Invalid quantity {quantity}")
        if slot_code in self.slots:
            raise ValueError(f"Slot already assigned {slot_code}")

        item = self._find_item(item_id)

        slot = SlotStock()
        slot.item = item
        slot.quantity = quantity
        self.slots[slot_code] = slot

    def restock_slot(self, slot_code: str, quantity: int):
        if slot_code.strip() == "":
            raise ValueError("Slot code is empty")
        if quantity <= 0:
            raise ValueError(f"Invalid quantity {quantity}")
        if slot_code not in self.slots:
            raise ValueError(f"Slot not assigned {slot_code}")

        slot = self.slots[slot_code]
        slot.quantity += quantity


class Machine:
    ACCEPTED_DENO = [0.25, 1, 5, 10]

    def __init__(self):
        self.inventory = Inventory()
        self.change_reserve: Dict[float, int] = {}
        self.current_transaction: List[float] = []
        self.lock = threading.Lock()

    def _get_inserted_total(self) -> float:
        return sum(self.current_transaction)

    def _to_cents(self, amount: float) -> int:
        return round(amount * 100)

    def _calculate_change(self, amount: float) -> Optional[Dict[float, int]]:
        remaining_cents = self._to_cents(amount)
        change_to_give: Dict[float, int] = {}

        denoms_desc = sorted(self.change_reserve.keys(), key=self._to_cents, reverse=True)

        for denom in denoms_desc:
            if remaining_cents <= 0:
                break

            denom_cents = self._to_cents(denom)
            available = self.change_reserve[denom]

            max_usable_by_amount = remaining_cents // denom_cents
            use_count = min(available, max_usable_by_amount)

            if use_count > 0:
                change_to_give[denom] = use_count
                remaining_cents -= denom_cents * use_count

        if remaining_cents != 0:
            return None

        return change_to_give

    def insert_money(self, val: float):
        with self.lock:
            if not isinstance(val, (int, float)) or val not in self.ACCEPTED_DENO:
                raise ValueError(f"Invalid transaction {val}")
            self.current_transaction.append(val)

    def select_item(self, slot_code: str):
        with self.lock:
            slot = self.inventory.slots.get(slot_code)
            if slot is None:
                raise ValueError(f"No such slot: {slot_code}.")
            if slot.quantity <= 0:
                raise ValueError(f"Slot {slot_code} is sold out.")

            price = slot.item.price
            inserted_total = self._get_inserted_total()

            if inserted_total < price:
                shortfall = price - inserted_total
                raise ValueError(f"Insufficient funds. Insert {shortfall} more.")

            change_owed = inserted_total - price
            change_to_give = self._calculate_change(change_owed)

            if change_to_give is None:
                self._refund_money()
                raise ValueError("Unable to dispense exact change. Transaction cancelled, money refunded.")

            item, change_given = self._dispense_item(slot_code, change_to_give)
            return item, change_given

    def cancel_transaction(self):
        with self.lock:
            return self._refund_money()

    def _dispense_item(self, slot_code: str, change_to_give: Dict[float, int]):
        slot = self.inventory.slots.get(slot_code)
        if slot is None:
            raise ValueError("Slot not found")

        slot.quantity -= 1

        for denom, count in change_to_give.items():
            self.change_reserve[denom] -= count

        for denom in self.current_transaction:
            self.change_reserve[denom] = (self.change_reserve.get(denom, 0) + 1)

        self.current_transaction = []

        return slot.item, change_to_give

    def _refund_money(self):
        refund = self.current_transaction
        self.current_transaction = []
        return refund
