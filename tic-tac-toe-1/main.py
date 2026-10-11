from player import Player
from game import Game


player1 = Player(
    "Raman",
    "X"
)

player2 = Player(
    "Aman",
    "O"
)

game = Game(
    player1,
    player2,
    3
)

game.start_game()