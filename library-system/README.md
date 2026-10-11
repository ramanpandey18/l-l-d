A Library System, at its simplest, is about books moving between a library's shelf and a member's hand. So the core actions are: add a book, search a book, borrow a book, return a book.

Here's a detailed requirement draft. Read through it and tell me what you'd change, add, or remove — that discussion is the design process.

Functional Requirements (draft)
Book Management
    The library has a catalog of books.
    Each book has: a title, an author, an ISBN (unique identifier), and a status (available / borrowed).
    The library can add a new book to the catalog.
    The library can remove a book from the catalog.
Member Management
    A library has registered members.
    Each member has: a name, a member ID, and a list of books they currently have borrowed.
    The library can register a new member.
Borrowing
    A member can borrow a book only if it's currently available.
    Once borrowed, the book's status changes to "borrowed," and it's added to that member's borrowed list.
    A member can only borrow if they haven't hit a maximum limit (say, 3 books at a time) — do you want this rule, or keep it unlimited for v1?
Returning
    A member can return a borrowed book.
    Once returned, the book becomes "available" again, and it's removed from the member's borrowed list.
Searching
    Someone can search the catalog by title or author.

Questions for you to decide (this is real LLD thinking):
    Should we track which member currently holds a specific book (so the library knows "this book is with Alice")? Or is it enough that the book just says "borrowed"?
    Do we enforce a max borrow limit per member, or skip that for v1?
    Do we need due dates / fines for late returns, or keep it simple (no time tracking) for now?
    Should there be multiple copies of the same book (e.g., 3 copies of "1984"), or assume every book is a single unique physical copy for now?
Test cases
    add_book — adding a valid book puts it in catalog
    add_book — empty title raises ValueError
    register_member — registering assigns a non-None id and adds to members
    register_member — empty name raises ValueError
    borrow_book — borrowing an available book: status becomes "borrowed", book appears in member's list
    borrow_book — borrowing a nonexistent/already-borrowed book raises ValueError
    borrow_book — borrowing with invalid member_id raises ValueError
    return_book — returning a borrowed book: status becomes "available", removed from member's list
    return_book — returning a book the member never borrowed raises ValueError