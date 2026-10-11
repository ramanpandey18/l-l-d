from datetime import date, timedelta
class LibraryBook:
    def __init__(self, book_id, title):
        self.book_id = book_id
        self.title = title
        self.__is_borrowed = False
        self.__due_date = None
    
    def borrow_book(self):
        if self.__is_borrowed == True:
            print("Book is already borrowed.")
            return False
        else:
            self.__is_borrowed = True
            self.__due_date = date.today() + timedelta(days=7)
            print("Book borrowed.")

    def return_book(self):
        if self.__is_borrowed == False:
            print("Book is not borrowed.")
            return False
        else:
            self.__is_borrowed = False
            self.__due_date = None
            print("Book returned.")

    def is_available(self):
        print("Inside is_available", {self.__is_borrowed}, {self.__due_date})
        if self.__is_borrowed == False:
            return True
        else:
            return False
    
book = LibraryBook(101, "Let Us Python")
print(book.is_available())
book.return_book()
book.borrow_book()
print(book.is_available())
book.return_book()
book.return_book()


# Exercise 3: LibraryBook Class
# Create a LibraryBook class with:

# Private: __is_borrowed, __due_date
# Public: title, book_id
# Methods: borrow_book(), return_book(), is_available()