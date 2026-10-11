import math
class Shape:
    def __init__(self):
        pass
    
    def area(self):
        pass

    def perimeter(self):
        pass

class Rectangle(Shape):
    def __init__(self, length, width):
        super().__init__()
        self.length = length
        self.width = width

    def area(self):
        a = self.length * self.width
        return round(a, 2)

    def perimeter(self):
        p = 2 * (self.length + self.width)
        return round(p, 2)

class Circle(Shape):
    def __init__(self, radius):
        super().__init__()
        self.radius = radius

    def area(self):
        a =  (math.pi * self.radius * self.radius)
        return round(a, 2)
              
    def perimeter(self):
        p = (2 * math.pi * self.radius)
        return round(p, 2)
 
class Triangle(Shape):
    def __init__(self, side1, side2, side3):
        super().__init__()
        self.side1 = side1
        self.side2 = side2
        self.side3 = side3

    def area(self):
        s = (self.side1 + self.side2 + self.side3) / 2
        area = math.sqrt(
            s *
            (s - self.side1) *
            (s - self.side2) *
            (s - self.side3)
        )
        return round(area, 2)
    
    def perimeter(self):
        p = self.side1 + self.side2 + self.side3
        return round(p, 2)
    
def print_shape_info(shape):
    print("Area:", shape.area())
    print("Perimeter:", shape.perimeter())
    
rectangle = Rectangle(10, 5)
circle = Circle(7)
triangle = Triangle(3, 4, 5)

print_shape_info(rectangle)

print("----------------")

print_shape_info(circle)

print("----------------")

print_shape_info(triangle)