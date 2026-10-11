from abc import ABC, abstractmethod
import math

class Shape(ABC):

    @abstractmethod
    def area(self):
        pass

    @abstractmethod
    def perimeter(self):
        pass

class Rectangle(Shape):
    def __init__(self, length, width):
        self.length = length
        self.width = width

    def area(self):
        a = self.length * self.width
        return round (a, 2)

    def perimeter(self):
        a = 2 * (self.length + self.width)
        return round (a, 2)


class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        a = math.pi * (self.radius * self.radius)
        return round(a, 2)

    def perimeter(self):
        s = 2 * math.pi * self.radius
        return round(s, 2)

class Square(Shape):
    def __init__(self, side):
        self.side = side
    
    def area(self):
        a = self.side * self.side
        return round(a, 2)
    
    def perimeter(self):
        p = 4 * self.side
        return round(p, 2)


shapes = [
    Rectangle(10, 5),
    Circle(7),
    Square(4)
]

for shape in shapes:
    print("Area:", shape.area())
    print("Perimeter:", shape.perimeter())
    print("----------------")