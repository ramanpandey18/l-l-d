class BankAccount0:
    def __init__(self, account_number, balance):
        self.account_number = account_number
        self.__balance = balance

    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
            return self.__balance

    def withdraw(self, amount):
        if amount > 0 and amount < self.__balance:
            self.__balance -= amount
            return self.__balance
        pass

    def get_balance(self):
        return self.__balance

account1 = BankAccount0(12345, 5000)
print(account1.get_balance())
print(account1.deposit(1000))
print(account1.withdraw(1100))
print(account1.get_balance())

account2 = BankAccount0(12345, 6000)
print(account2.get_balance())
print(account2.deposit(500))
print(account2.withdraw(400))
print(account2.get_balance())