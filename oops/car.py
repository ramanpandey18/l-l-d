class Car:
    def __init__(self, brand, model, year):
        self. brand = brand
        self.model = model
        self.year = year
        self.speed = 0
    
    def accelerate(self):
        self.speed += 20
        print(f"{self.brand} {self.model} {self.year} is accelerating at speed {self.speed}.")
    

my_car = Car("Tata", "Harrier", "2027")
my_car.accelerate()


class Dog:
    pass

dog1 = Dog()
dog2 = Dog()
print(type(dog1))