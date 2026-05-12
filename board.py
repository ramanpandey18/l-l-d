class Board:
    def __init__(self, size):
        self.size = size
        self.grid = [[" " for _ in range(size)] for _ in range(size)]

    def print_board(self):
        for row in self.grid:
            print(" | ".join(row))
        print("-" * (self.size * 4 - 1))

    def is_valid_move(self, row, col):
        return (
            0 <= row < self.size and
            0 <= col < self.size and
            self.grid[row][col] == " "
        )

    def place_move(self, row, col, symbol):
        if self.is_valid_move(row, col):
            self.grid[row][col] = symbol
            return True
        return False

    def check_winner(self, symbol):
        for row in self.grid:
            if all(cell == symbol for cell in row):
                return True
        
        for col in range(self.size):
            if all(self.grid[row][col] == symbol for row in range(self.size)):
                return True
        
        if all(self.grid[i][i] == symbol for i in range(self.size)):
            return True
    
        if all(self.grid[i][self.size - 1 - i] == symbol for i in range(self.size)):
            return True
    
    def is_full(self):
        for row in self.grid:
            if " " in row:
                return False
        return True
