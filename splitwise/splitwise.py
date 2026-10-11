import heapq
import threading
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


def fmt(paise: int) -> str:
    return f"₹{paise // 100}.{paise % 100:02d}"


# ====================== MODELS ======================

class User:
    def __init__(self, name: str, id: str = None):
        self.name = name
        self.id = id if id is not None else str(uuid.uuid4())

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.name!r})"


class Split:
    def __init__(self, user: User, amount: int):
        self.user = user
        self.amount = amount  # paise

    def __repr__(self):
        return f"Split(user={self.user.name!r}, amount={self.amount})"


class SplitType(Enum):
    EQUAL = "EQUAL"
    EXACT = "EXACT"
    PERCENT = "PERCENT"


class Expense:
    def __init__(self, paid_by: User, total_amount: int, splits: list, description: str = ""):
        if total_amount <= 0:
            raise ValueError("Amount must be positive")
        if sum(s.amount for s in splits) != total_amount:
            raise ValueError("Splits must sum to the total amount")

        self.id = str(uuid.uuid4())
        self.paid_by = paid_by
        self.total_amount = total_amount
        self.splits = splits
        self.description = description
        self.created_at = datetime.now()

    def __repr__(self):
        return (
            f"Expense(id={self.id[:8]}, paid_by={self.paid_by.name!r}, "
            f"total={fmt(self.total_amount)}, description={self.description!r})"
        )


# ====================== STRATEGIES ======================

class SplitStrategy(ABC):
    @abstractmethod
    def calculate(self, total: int, participants: list, metadata=None) -> list:
        """Return who owes how much. Amounts must sum to total."""


class EqualSplit(SplitStrategy):
    def calculate(self, total, participants, metadata=None):
        if total <= 0:
            raise ValueError("Amount must be positive")
        if not participants:
            raise ValueError("Need at least one participant")

        base, remainder = divmod(total, len(participants))
        return [
            Split(user, base + (1 if i < remainder else 0))
            for i, user in enumerate(participants)
        ]


class ExactSplit(SplitStrategy):
    """metadata = exact amounts in paise, same order as participants."""

    def calculate(self, total, participants, metadata=None):
        if total <= 0:
            raise ValueError("Amount must be positive")
        if not participants:
            raise ValueError("Need at least one participant")
        if metadata is None or len(metadata) != len(participants):
            raise ValueError("Provide one exact amount per participant")
        if any(a < 0 for a in metadata):
            raise ValueError("Amounts cannot be negative")
        if sum(metadata) != total:
            raise ValueError("Exact amounts must sum to the total")

        return [Split(user, amt) for user, amt in zip(participants, metadata)]


class PercentSplit(SplitStrategy):
    """metadata = percentages in basis points (100% = 10000)."""

    def calculate(self, total, participants, metadata=None):
        if total <= 0:
            raise ValueError("Amount must be positive")
        if not participants:
            raise ValueError("Need at least one participant")
        if metadata is None or len(metadata) != len(participants):
            raise ValueError("Provide one percentage per participant")
        if any(bp < 0 for bp in metadata):
            raise ValueError("Percentages cannot be negative")
        if sum(metadata) != 10000:
            raise ValueError("Percentages must sum to 100%")

        amounts = [total * bp // 10000 for bp in metadata]
        leftover = total - sum(amounts)
        for i in range(leftover):
            amounts[i] += 1

        return [Split(user, amt) for user, amt in zip(participants, amounts)]


class SplitStrategyFactory:
    def __init__(self):
        self._strategies = {
            SplitType.EQUAL: EqualSplit(),
            SplitType.EXACT: ExactSplit(),
            SplitType.PERCENT: PercentSplit(),
        }

    def get_strategy(self, split_type: SplitType) -> SplitStrategy:
        strategy = self._strategies.get(split_type)
        if strategy is None:
            raise ValueError(f"Unsupported split type: {split_type}")
        return strategy


# ====================== BALANCE SHEET ======================

class BalanceSheet:
    """
    _balances = {debtor: {creditor: amount}}
    Only ONE direction is stored per pair (A owes B 50 and B owes A 20 -> A owes B 30).
    """

    def __init__(self):
        self._balances = {}
        self._lock = threading.RLock()

    # ---- internal helpers ----
    def _get(self, debtor, creditor):
        return self._balances.get(debtor, {}).get(creditor, 0)

    def _set(self, debtor, creditor, amount):
        if amount == 0:
            row = self._balances.get(debtor)
            if row and creditor in row:
                del row[creditor]
                if not row:
                    del self._balances[debtor]
        else:
            self._balances.setdefault(debtor, {})[creditor] = amount

    # ---- public API ----
    def add_debt(self, debtor: User, creditor: User, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if debtor == creditor:
            return
        with self._lock:
            reverse = self._get(creditor, debtor)
            if reverse >= amount:
                # existing opposite debt absorbs this one
                self._set(creditor, debtor, reverse - amount)
            else:
                # wipe the opposite debt, remainder goes in forward direction
                self._set(creditor, debtor, 0)
                self._set(debtor, creditor, self._get(debtor, creditor) + amount - reverse)

    def get_balance(self, a: User, b: User) -> int:
        """Positive: a owes b. Negative: b owes a."""
        with self._lock:
            return self._get(a, b) - self._get(b, a)

    def get_user_balances(self, user: User) -> dict:
        """{other_user: signed amount}. Positive: user owes other. Negative: other owes user."""
        with self._lock:
            result = {}
            for debtor, row in self._balances.items():
                for creditor, amt in row.items():
                    if debtor == user:
                        result[creditor] = amt
                    elif creditor == user:
                        result[debtor] = -amt
            return result

    def net_balance(self, user: User) -> int:
        """Positive: user is owed money overall. Negative: user owes money overall."""
        with self._lock:
            return -sum(self.get_user_balances(user).values())

    def all_debts(self) -> list:
        with self._lock:
            return [
                (debtor, creditor, amt)
                for debtor, row in self._balances.items()
                for creditor, amt in row.items()
            ]

    def users(self) -> list:
        with self._lock:
            seen = {}
            for debtor, creditor, _ in self.all_debts():
                seen[debtor] = True
                seen[creditor] = True
            return list(seen)

    def show(self):
        debts = self.all_debts()
        if not debts:
            print("All settled up!")
        for debtor, creditor, amt in debts:
            print(f"{debtor.name} owes {creditor.name}: {fmt(amt)}")


# ====================== GROUP ======================

class Group:
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.members = []
        self.expenses = []
        self.balance_sheet = BalanceSheet()   # balances are scoped per group
        self.lock = threading.RLock()

    def add_member(self, user: User):
        with self.lock:
            if user not in self.members:
                self.members.append(user)

    def add_expense(self, expense: Expense):
        with self.lock:
            self.expenses.append(expense)

    def is_member(self, user: User) -> bool:
        return user in self.members


# ====================== SERVICES ======================

class ExpenseService:
    def __init__(self, strategy_factory: SplitStrategyFactory = None):
        self.strategy_factory = strategy_factory or SplitStrategyFactory()

    def add_expense(self, group: Group, paid_by: User, total: int, participants: list,
                    split_type: SplitType, metadata=None, description: str = "") -> Expense:
        # validations
        if not group.is_member(paid_by):
            raise ValueError(f"{paid_by.name} is not in the group")
        for p in participants:
            if not group.is_member(p):
                raise ValueError(f"{p.name} is not in the group")

        strategy = self.strategy_factory.get_strategy(split_type)
        splits = strategy.calculate(total, participants, metadata)
        expense = Expense(paid_by, total, splits, description)

        # one lock for the whole update so balances never get half-applied
        with group.lock:
            for split in splits:
                if split.user != paid_by and split.amount > 0:
                    group.balance_sheet.add_debt(split.user, paid_by, split.amount)
            group.add_expense(expense)
        return expense

    def show_balances(self, group: Group):
        print(f"--- Balances in '{group.name}' ---")
        group.balance_sheet.show()


class SettlementService:
    def settle(self, group: Group, payer: User, receiver: User, amount: int):
        """payer pays `amount` to receiver, reducing what payer owes receiver."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        with group.lock:
            owed = group.balance_sheet.get_balance(payer, receiver)
            if owed <= 0:
                raise ValueError(f"{payer.name} does not owe {receiver.name}")
            if amount > owed:
                raise ValueError(f"Cannot settle more than owed ({fmt(owed)})")
            # recording "receiver owes payer" cancels the existing debt
            group.balance_sheet.add_debt(receiver, payer, amount)


class DebtSimplifier:
    """Min-cash-flow: at most n-1 transactions. Does NOT modify the balance sheet."""

    def simplify(self, balance_sheet: BalanceSheet) -> list:
        creditors = []  # max-heap via negative amounts
        debtors = []    # max-heap via negative amounts (stored as amount owed, negated)

        for i, user in enumerate(balance_sheet.users()):
            net = balance_sheet.net_balance(user)
            if net > 0:
                heapq.heappush(creditors, (-net, i, user))
            elif net < 0:
                heapq.heappush(debtors, (net, i, user))   # net already negative

        transactions = []
        while creditors and debtors:
            c_neg, ci, creditor = heapq.heappop(creditors)
            d_neg, di, debtor = heapq.heappop(debtors)
            credit, debt = -c_neg, -d_neg

            pay = min(credit, debt)
            transactions.append((debtor, creditor, pay))

            if credit > pay:
                heapq.heappush(creditors, (-(credit - pay), ci, creditor))
            if debt > pay:
                heapq.heappush(debtors, (-(debt - pay), di, debtor))

        return transactions


# ====================== DEMO ======================

if __name__ == "__main__":
    a, b, c = User("A"), User("B"), User("C")

    group = Group("Goa Trip")
    for u in (a, b, c):
        group.add_member(u)

    expense_service = ExpenseService()
    settlement_service = SettlementService()
    simplifier = DebtSimplifier()

    # A pays 100.00 for dinner, split equally among A, B, C
    expense_service.add_expense(group, a, 10000, [a, b, c], SplitType.EQUAL, description="Dinner")
    # B pays 30.00 for cab, split equally between A and B
    expense_service.add_expense(group, b, 3000, [a, b], SplitType.EQUAL, description="Cab")
    # C pays 90.00 for hotel, split 50/30/20
    expense_service.add_expense(group, c, 9000, [a, b, c], SplitType.PERCENT,
                                metadata=[5000, 3000, 2000], description="Hotel")

    expense_service.show_balances(group)

    print("\nSimplified:")
    for debtor, creditor, amt in simplifier.simplify(group.balance_sheet):
        print(f"{debtor.name} pays {creditor.name}: {fmt(amt)}")

    print("\nB settles ₹10.00 with A")
    settlement_service.settle(group, b, a, 1000)
    expense_service.show_balances(group)

    try:
        settlement_service.settle(group, b, a, 999999)
    except ValueError as e:
        print("OK:", e)

# add_expense(group, paid_by, total, participants, split_type, metadata)
#    |
#    |-- 1. validate: payer and participants are group members
#    |-- 2. SplitStrategyFactory.get_strategy(split_type)   -> EqualSplit / ExactSplit / PercentSplit
#    |-- 3. strategy.calculate(total, participants, meta)   -> list[Split]  (integer paise, sums to total)
#    |-- 4. Expense(paid_by, total, splits)                 -> validated record
#    |-- 5. under group.lock:
#    |       for each split where user != payer:
#    |           BalanceSheet.add_debt(split.user, payer, split.amount)
#    |       group.add_expense(expense)
#    |
# show_balances(group)         -> prints "X owes Y: ₹amount"
# settle(group, payer, recv)   -> checks payer really owes recv, then cancels that debt in the BalanceSheet
# simplify(balance_sheet)      -> net balance per user -> heaps of creditors/debtors -> min transactions