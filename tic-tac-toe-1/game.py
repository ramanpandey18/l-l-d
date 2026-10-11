from board import Board
from player import Player

class Game:
    def __init__(self, player1, player2, size):
        self.players = [player1, player2]
        self.board = Board(size)
        self.current_player_index = 0
        self.game_over = False
        self.winner = None

    def switch_player(self):
        self.current_player_index = 1 - self.current_player_index
    
    def get_current_player(self):
        return self.players[self.current_player_index]
    
    def play_move(
        self,
        row,
        col
    ):
        current_player = (
            self.get_current_player()
        )

        success = self.board.place_move(
            row,    
            col,
            current_player.symbol
        )

        if not success:

            print("Invalid move.")

            return False

        if self.check_winner(
            current_player.symbol
        ):

            self.game_over = True

            self.winner = current_player

            print(
                f"{current_player.name} wins!"
            )

        elif self.check_draw():

            self.game_over = True

            print("Game is a draw.")

        else:

            self.switch_player()

        return True

    def check_winner(self, symbol):

        grid = self.board.grid

        size = self.board.size

        # Check rows
        for row in grid:

            if all(cell == symbol for cell in row):
                return True

        # Check columns
        for col in range(size):

            if all(
                grid[row][col] == symbol
                for row in range(size)
            ):
                return True

        # Check main diagonal
        if all(
            grid[i][i] == symbol
            for i in range(size)
        ):
            return True

        # Check opposite diagonal
        if all(
            grid[i][size - 1 - i] == symbol
            for i in range(size)
        ):
            return True

        return False


    def check_draw(self):
        for row in self.board.grid:

            if " " in row:
                return False

        return True

    def start_game(self):

        while not self.game_over:

            self.board.print_board1()

            current_player = (
                self.get_current_player()
            )

            print(
                f"\n{current_player.name}'s turn "
                f"({current_player.symbol})"
            )

            row = int(input("Enter row: "))

            col = int(input("Enter col: "))

            self.play_move(row, col)

            print("-------------------")

        self.board.print_board1()

        if self.winner:

            print(
                f"{self.winner.name} won the game!"
            )

        else:

            print("Game ended in a draw.")