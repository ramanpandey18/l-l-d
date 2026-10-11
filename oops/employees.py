class Employees:
    def __init__(self, employee_id, name, salary):
        self.employee_id = employee_id
        self.name = name
        self._salary = salary
    
    def get_details(self):
        print(f"Employee ID: {self.employee_id}")
        print(f"Name: {self.name}")
        print(f"Salary: {self._salary}")

    def calculate_bonus(self):
        bonus = round((self._salary * 10) / 100, 2)
        return bonus

class Manager(Employees):
    def __init__(self, employee_id, name, salary, department):
        super().__init__(employee_id, name, salary)
        self.department = department
        self.tasks = []

    def assign_task(self, task):
        if not task or task.strip() == "":
            print("❌ Invalid task!")
            return False
        
        if task in self.tasks:
            print(f"⚠️ Task '{task}' already assigned.")
            return False
        
        self.tasks.append(task)
        print(f"✅ Task '{task}' assigned to Manager {self.name}.")
        return True
    
    def calculate_bonus(self):
        bonus = round((self._salary * 20) / 100, 2)
        return bonus
    
class Developer(Employees):
    def __init__(self, employee_id, name, salary, programming_language):
        super().__init__(employee_id, name, salary)
        self.programming_language = programming_language
    
    def calculate_bonus(self):
        bonus = round((self._salary * 15) / 100, 2)
        return bonus

    def write_code(self, lines_of_code):
        if lines_of_code <= 0:
            print("❌ Lines of code must be greater than zero.")
            return False
        
        print(f"💻 {self.name} wrote {lines_of_code} lines of code in {self.programming_language}.")
        return True

print("=== Manager ===")
manager = Manager(101, "Aman", 100000, "Engineering")
manager.get_details()
print(f"Bonus: ₹{manager.calculate_bonus():,}\n")

manager.assign_task("Prepare Sprint Report")
manager.assign_task("Prepare Sprint Report")   # Duplicate test

print("\n=== Developer ===")
developer = Developer(102, "Raman", 80000, "Python")
developer.get_details()
print(f"Bonus: ₹{developer.calculate_bonus():,}\n")

developer.write_code(450)
