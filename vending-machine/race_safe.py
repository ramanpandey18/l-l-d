"""
Two threads race to buy the LAST item in a slot with quantity=1.
Without a correctly-placed lock, both could pass the "in stock" check
before either updates the quantity, resulting in the item being
"dispensed" twice from a single unit of stock.
"""
import threading
from vending_machine import Item, Machine

machine = Machine()
item_id = machine.inventory.add_item(Item("Coke", 1.00))
machine.inventory.assign_slot("A1", item_id, quantity=1)  # only ONE left
machine.change_reserve = {10: 5, 5: 5, 1: 20, 0.25: 20}

results = {}

def try_buy(name):
    try:
        # each "customer" is a separate machine call inserting exact change
        machine.insert_money(1)
        item, change = machine.select_item("A1")
        results[name] = f"SUCCESS - got {item.name}, change={change}"
    except ValueError as e:
        results[name] = f"FAILED - {e}"

t1 = threading.Thread(target=try_buy, args=("Customer A",))
t2 = threading.Thread(target=try_buy, args=("Customer B",))
t1.start()
t2.start()
t1.join()
t2.join()

print("--- Results ---")
for name, outcome in results.items():
    print(f"{name}: {outcome}")

success_count = sum(1 for v in results.values() if v.startswith("SUCCESS"))
print(f"\nFinal slot quantity: {machine.inventory.slots['A1'].quantity}")
print(f"Number of successful purchases: {success_count}")
print(f"Correct (should be exactly 1): {success_count == 1}")
