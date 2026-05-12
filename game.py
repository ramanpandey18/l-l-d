from board import Board
from player import Player

class Game:
    def __init__(self, size, player1, player2):
        self.board = Board(size)
        self.players = [player1, player2]
        self.current_player_index = 0
    
    def switch_player(self):
        self.current_player_index = 1 - self.current_player_index

    def play(self):

        while True:

            self.board.print_board()

            player = self.players[self.current_player_index]

            print(f"{player.name}'s turn ({player.symbol})")

            row = int(input("Enter row: "))
            col = int(input("Enter col: "))

            if not self.board.place_move(row, col, player.symbol):
                print("Invalid move!")
                continue

            if self.board.check_winner(player.symbol):
                self.board.print_board()
                print(f"{player.name} wins!")
                break

            if self.board.is_full():
                self.board.print_board()
                print("It's a draw!")
                break

            self.switch_player()


player1 = Player("Raman", "X")
player2 = Player("Aman", "O")

game = Game(3, player1, player2)
game.play()