import threading
import pytest

from splitwise import (
    User, Group, SplitType, SplitStrategyFactory, Expense, Split,
    EqualSplit, ExactSplit, PercentSplit,
    BalanceSheet, ExpenseService, SettlementService, DebtSimplifier,
)


@pytest.fixture
def setup():
    a, b, c = User("A"), User("B"), User("C")
    group = Group("Trip")
    for u in (a, b, c):
        group.add_member(u)
    return a, b, c, group, ExpenseService(), SettlementService(), DebtSimplifier()


# ---------- strategies ----------

def test_equal_split_leftover():
    a, b, c = User("A"), User("B"), User("C")
    amounts = [s.amount for s in EqualSplit().calculate(10000, [a, b, c])]
    assert amounts == [3334, 3333, 3333]


def test_exact_split_rejects_wrong_sum():
    a, b = User("A"), User("B")
    with pytest.raises(ValueError):
        ExactSplit().calculate(1000, [a, b], [600, 300])


def test_exact_split_rejects_negative():
    a, b = User("A"), User("B")
    with pytest.raises(ValueError):
        ExactSplit().calculate(1000, [a, b], [1500, -500])


def test_percent_split_leftover():
    a, b, c = User("A"), User("B"), User("C")
    amounts = [s.amount for s in PercentSplit().calculate(100, [a, b, c], [3333, 3333, 3334])]
    assert amounts == [34, 33, 33]
    assert sum(amounts) == 100


def test_percent_split_rejects_not_100():
    a, b = User("A"), User("B")
    with pytest.raises(ValueError):
        PercentSplit().calculate(1000, [a, b], [5000, 4000])


def test_factory_unsupported_type():
    with pytest.raises(ValueError):
        SplitStrategyFactory().get_strategy("NOPE")


# ---------- expense ----------

def test_expense_rejects_mismatched_splits():
    a, b = User("A"), User("B")
    with pytest.raises(ValueError):
        Expense(a, 1000, [Split(a, 400), Split(b, 400)])


# ---------- balance sheet ----------

def test_balance_sheet_normalizes_direction():
    a, b = User("A"), User("B")
    bs = BalanceSheet()
    bs.add_debt(a, b, 50)
    bs.add_debt(b, a, 20)
    assert bs.get_balance(a, b) == 30
    assert len(bs.all_debts()) == 1


def test_balance_sheet_full_cancel():
    a, b = User("A"), User("B")
    bs = BalanceSheet()
    bs.add_debt(a, b, 50)
    bs.add_debt(b, a, 50)
    assert bs.all_debts() == []


# ---------- expense service ----------

def test_non_member_rejected(setup):
    a, b, c, group, es, *_ = setup
    outsider = User("X")
    with pytest.raises(ValueError):
        es.add_expense(group, a, 1000, [a, outsider], SplitType.EQUAL)


def test_payer_not_in_participants(setup):
    a, b, c, group, es, *_ = setup
    es.add_expense(group, a, 10000, [b, c], SplitType.EQUAL)
    assert group.balance_sheet.get_balance(b, a) == 5000
    assert group.balance_sheet.get_balance(c, a) == 5000


# ---------- end to end ----------

def build_scenario(setup):
    a, b, c, group, es, *_ = setup
    es.add_expense(group, a, 10000, [a, b, c], SplitType.EQUAL, description="Dinner")
    es.add_expense(group, b, 3000, [a, b], SplitType.EQUAL, description="Cab")
    es.add_expense(group, c, 9000, [a, b, c], SplitType.PERCENT,
                   metadata=[5000, 3000, 2000], description="Hotel")


def test_end_to_end_balances(setup):
    a, b, c, group, *_ = setup
    build_scenario(setup)
    bs = group.balance_sheet
    assert bs.get_balance(b, a) == 1833
    assert bs.get_balance(a, c) == 1167
    assert bs.get_balance(b, c) == 2700
    assert len(group.expenses) == 3


def test_net_balances_sum_to_zero(setup):
    a, b, c, group, *_ = setup
    build_scenario(setup)
    bs = group.balance_sheet
    assert sum(bs.net_balance(u) for u in bs.users()) == 0


def test_simplify(setup):
    a, b, c, group, es, ss, simp = setup
    build_scenario(setup)
    txns = {(d.name, cr.name, amt) for d, cr, amt in simp.simplify(group.balance_sheet)}
    assert txns == {("B", "C", 3867), ("B", "A", 666)}


def test_simplify_does_not_mutate(setup):
    a, b, c, group, es, ss, simp = setup
    build_scenario(setup)
    before = sorted((d.name, cr.name, amt) for d, cr, amt in group.balance_sheet.all_debts())
    simp.simplify(group.balance_sheet)
    after = sorted((d.name, cr.name, amt) for d, cr, amt in group.balance_sheet.all_debts())
    assert before == after


# ---------- settlement ----------

def test_partial_settlement(setup):
    a, b, c, group, es, ss, simp = setup
    build_scenario(setup)
    ss.settle(group, b, a, 1000)
    assert group.balance_sheet.get_balance(b, a) == 833


def test_settle_more_than_owed(setup):
    a, b, c, group, es, ss, simp = setup
    build_scenario(setup)
    with pytest.raises(ValueError):
        ss.settle(group, b, a, 999999)


def test_settle_when_nothing_owed(setup):
    a, b, c, group, es, ss, simp = setup
    with pytest.raises(ValueError):
        ss.settle(group, a, b, 100)


# ---------- concurrency ----------

def test_concurrent_expenses(setup):
    a, b, c, group, es, *_ = setup

    def worker():
        es.add_expense(group, a, 1000, [a, b], SplitType.EQUAL)

    threads = [threading.Thread(target=worker) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert group.balance_sheet.get_balance(b, a) == 50 * 500
    assert len(group.expenses) == 50
