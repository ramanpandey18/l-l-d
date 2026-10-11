Final Requirements — Vending Machine v1
Slots — each has a code, item name, price, and quantity. 
Multiple slots can hold the same item.
Denominations accepted: $0.25, $1, $5, $10 — insert_money(amount) called once per bill/coin, 
validated against this set, accumulating a running total for the current transaction.
Machine's own change reserve — the machine starts with some initial stock of each denomination, and every inserted coin/bill also gets added to this reserve (so it "learns" more currency over time, like a real machine).
Selecting an item (select_item(code)):
Slot must exist and be in stock → else reject.
Inserted total must be ≥ price → else reject, tell them how much more is needed.
Change owed = inserted total − price. The machine must be able to make exact change using its reserve (greedy: largest denominations first) → if it can't, refuse the sale and refund everything inserted, and don't touch the reserve.
If everything checks out: dispense the item, reduce slot quantity, deduct the dispensed change denominations from the reserve, reset the transaction.
Cancel/refund (cancel()) — at any point before dispensing, return all inserted money (as denominations) and reset the transaction.
States: Idle (no money inserted) → Has Money (money inserted, awaiting selection) → back to Idle after a successful dispense or a cancel.
Concurrency — explicitly deferred to a later enhancement pass, same as we did for Library.

1. slot can be a enum or dict.
classes
Machine


Inventory