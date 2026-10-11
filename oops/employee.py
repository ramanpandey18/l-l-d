class Employee:
    engineering = 10
    sales = 10
    security = 12
    BONUS_PERCENTAGES = {
        "engineering": 20,
        "sale": 15,
        "security": 10
    }
    
    def __init__(self, employee_id, name, department):
        self.employee_id = employee_id
        self.name = name
        self._department = department
        self.__salary = 0

    def set_salary(self, salary):
        if salary <= 0:
            return False
        self.__salary = salary
        print("Salary set successfully")
        return True

    def get_salary(self):
        return self.__salary

    def give_raise(self, percent):
        if percent > 0 and percent <= 100:
            raised_amount = round(((self.__salary * percent) / 100), 2)
            if raised_amount <= 0:
                return False
            self.__salary += raised_amount
        else:
            return False

    def _calculate_bonus(self):
        bonus_percent = self.BONUS_PERCENTAGES.get(self._department, 0)
        if bonus_percent >= 0:
            bonus = round(((self.__salary * bonus_percent) / 100), 2)
            return bonus
        return 0

employee = Employee("251", "Raman", "engineering")
print(employee.get_salary())
employee.set_salary(100000)
print(employee.get_salary())
employee.give_raise(20)
print(employee.get_salary())
print(employee._calculate_bonus())
# Exercise 2: Employee Class
# Create an Employee class with:

# Private: __salary
# Protected: _department
# Public: employee_id, name
# Methods:
# give_raise(percentage)
# get_salary()
# _calculate_bonus() (protected method)