class Student:
    def __init__(self, name, roll_number, marks):
        self.name = name
        self.roll_number = roll_number
        self.marks = marks
    
    def get_average(self):
        return (sum(self.marks) / len(self.marks))

    def is_passed(self):
        return self.get_average() >= 40
    
    def has_failed_subject(self):
        for mark in self.marks:
            if mark < 40:
                return True
        return False


student1 = Student("ABC", 1, [70, 20, 90])
student2 = Student("XYZ", 2, [80, 30, 90])

print(student1.get_average())
print(student1.is_passed())
print(student1.has_failed_subject())

print(student1.get_average())
print(student1.is_passed())
print(student2.has_failed_subject())
