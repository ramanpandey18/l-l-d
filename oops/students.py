class Students:
    def __init__(self, name, roll_number):
        self.roll_number = roll_number
        self._name = name
        self.__marks = []
    
    def add_mark(self, subject, score):
        self.__marks.append({
            "subject": subject,
            "score": score
        })

    def get_average(self):
        if len(self.__marks) == 0:
            return 0
        total = 0
        for mark in self.__marks:
            total += mark["score"]
        return round((total / len(self.__marks)), 2)

    def get_name(self):
        return self._name

    def set_name(self, new_name):
        self._name = new_name

   
student = Students("Raman", 18)
student.add_mark("Physics", 75)
student.add_mark("Chemistry", 60)
student.add_mark("Maths", 65)

print(student.get_name())
print(student.get_average())
student.set_name("Raman Pandey")
print(student.get_name())
   
    # add_mark(subject, score)
    # get_average()
    # get_name() (getter)
    # set_name(new_name) (setter)