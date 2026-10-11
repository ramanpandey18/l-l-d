class Vehicle:
    def __init__(self, brand, year):
        self.brand = brand
        self.year = year

    def start(self):
        print(f"{self.brand} Vehicle is starting...")

    def stop(self):
        print(f"{self.brand} Vehicle has stopped!")


class Car(Vehicle):
    def __init__(self, brand, year, doors):
        super().__init__(brand, year)
        self.num_doors = doors
    
    def start(self):
        print(f"{self.brand} car with {self.num_doors} doors started smoothly.")

class Bike(Vehicle):
    def __init__(self, brand, year, side_car):
        super().__init__(brand, year)
        self.has_sidecar = side_car
    
    def wheelie(self):
        if self.has_sidecar:
            print(f"{self.brand} bike cannot do wheelie with sidecar!")
        else:
            print(f"{self.brand} bike is doing a wheelie.")

    def stop(self):
        print(f"{self.brand} bike has stopped safely.")

car = Car("Tata", 2020, 4)
print(car.brand)
print(car.year)
car.start()
car.stop()
# print(car.num_doors)
print(f"{car.brand} car has how many doors ? {car.num_doors}")

bike = Bike("Royal Enfield", 2023, False)
print(bike.brand)
print(bike.year)
bike.start()
bike.stop()
bike.wheelie()
print(bike.has_sidecar)
print(f"Does bike have sidecar? {bike.has_sidecar}")

bike = Bike("Harley Davidson", 2025, True)
print(bike.brand)
print(bike.year)
bike.start()
bike.stop()
bike.wheelie()
# print(bike.has_sidecar)
print(f"Does bike have sidecar? {bike.has_sidecar}")

# Exercise 1: Vehicle Hierarchy
# Create a class Vehicle (parent) with:

# Attributes: brand, year
# Methods: start(), stop()

# Create two child classes:

# Car(Vehicle) → add num_doors, override start()
# Bike(Vehicle) → add has_sidecar, add method wheelie()