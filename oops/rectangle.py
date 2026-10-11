class Rectangle:
    def __init__(self, length, width):
        self.length = length
        self.width = width

    def perimeter(self):
        p = 2 * (self.length + self.width)
        return p
    
    def area(self):
        a = (self.length * self.width)
        return a

rectangle1 = Rectangle(20, 24)
print(rectangle1.area())
print(rectangle1.perimeter())

rectangle2 = Rectangle(16, 20)
print(rectangle2.area())
print(rectangle2.perimeter())