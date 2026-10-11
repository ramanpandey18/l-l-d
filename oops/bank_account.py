class BankAccount:
    def __init__(self, account_number, balance):
        self.account_number = account_number
        self._balance = balance

    def deposit(self, amount):
        if amount <= 0:
            print(f"❌ Invalid deposit amount: ₹{amount}")
            return False
        else:
            self._balance += amount
            print(f"✅ ₹{amount} deposited successfully. New Balance: ₹{self._balance}")
            return True

    def withdraw(self, amount):
        if amount <= 0:
            print("❌ Amount must be greater than zero.")
            return False
        
        if amount > self._balance:
            print("❌ Insufficient balance!")
            return False
        self._balance -= amount
        print(f"✅ ₹{amount} withdrawn successfully. New Balance: ₹{self._balance}")
        return True

    def get_balance(self):
        return self._balance

class SavingsAccount(BankAccount):
    def __init__(self, account_number, balance):
        super().__init__(account_number, balance)
        self.interest_rate = 4.5
    
    def add_interest(self):
        interest = round(self._balance * 0.045, 2)
        self._balance += interest
        print(f"✅ Interest of ₹{interest} added at {self.interest_rate}% rate.")

class CurrentAccount(BankAccount):
    def __init__(self, account_number, balance):
        super().__init__(account_number, balance)
        self.overdraft_limit = 10000

    def withdraw(self, amount):
        if amount <= 0:
            print("❌ Amount must be greater than zero.")
            return False

        max_allowed = self._balance + self.overdraft_limit
        
        if amount > max_allowed:
            print(f"❌ Cannot withdraw ₹{amount}. Overdraft limit exceeded!")
            return False

        self._balance -= amount
        print(f"✅ ₹{amount} withdrawn successfully (Current Balance: ₹{self._balance})")
        return True

# Testing SavingsAccount

savings = SavingsAccount(101, 5000)

print("Initial Savings Balance:", savings.get_balance())

savings.deposit(2000)

savings.withdraw(1000)

savings.add_interest()

print("Final Savings Balance:", savings.get_balance())


print("\n-----------------------\n")


# Testing CurrentAccount

current = CurrentAccount(201, 5000)

print("Initial Current Balance:", current.get_balance())

current.withdraw(12000)

print("Balance After Overdraft Withdrawal:", current.get_balance())

current.deposit(3000)

print("Balance After Deposit:", current.get_balance())

current.withdraw(4000)

print("Final Current Balance:", current.get_balance())