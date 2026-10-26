class Board:
    def __init__(self, size):
        self.size = size
        self.grid = [[" " for _ in range(size)] for _ in range(size)]

    def print_board(self):
        for i, row in enumerate(self.grid):
            print(" | ".join(row))
            if i != self.size - 1:
                print("-" * (self.size * 4 - 3))

    def is_valid_move(self, row, col):
        return (
            0 <= row < self.size
            and 0 <= col < self.size
            and self.grid[row][col] == " "
        )

    def place_move(self, row, col, symbol):
        if self.is_valid_move(row, col):
            self.grid[row][col] = symbol
            return True
        return False
