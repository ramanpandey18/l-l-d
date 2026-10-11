from abc import ABC, abstractmethod

class Employee(ABC):

    @abstractmethod
    def calculate_salary(self):
        pass

    @abstractmethod
    def get_role(self):
        pass


class FullTimeEmployee(Employee):
    def __init__(self, name, employee_id, monthly_salary):
        self.name = name
        self.employee_id = employee_id
        self.monthly_salary = monthly_salary
    
    def calculate_salary(self):
        return self.monthly_salary

    def get_role(self):
        return "Full Time Employee"

class ContractEmployee(Employee):
    def __init__(self, name, employee_id, hourly_rate, hours_worked):
        self.name = name
        self.employee_id = employee_id
        self.hourly_rate = hourly_rate
        self.hours_worked = hours_worked

    def calculate_salary(self):
        salary = self.hours_worked * self.hourly_rate
        return round(salary, 2)
    
    def get_role(self):
        return "Contract Employee"

def display_employee_info(employee):
    print(f"Employee ID : {employee.employee_id}")
    print(f"Name        : {employee.name}")
    print(f"Role        : {employee.get_role()}")
    print(f"Salary      : ₹{employee.calculate_salary():,}")
    print("-" * 40)


employee1 = FullTimeEmployee(
    "Raman",
    101,
    120000
)

employee2 = ContractEmployee(
    "Aman",
    102,
    500,
    160
)

employee3 = ContractEmployee(
    "Rahul",
    103,
    800,
    100
)

display_employee_info(employee1)

display_employee_info(employee2)

display_employee_info(employee3)