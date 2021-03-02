'''
Homework 1 Rock Scissors Paper game
24/02/21
Jesús A Bermúdez Silva
'''
import random

'''
obtains user's choice and generates computer's choice
'''
def getChoices():
    computerChose = random.choice(["rock", "paper", "scissors"])
    userChose = input("Enter choice [rock, paper, scissors]: ")
    while userChose != "rock" and userChose != "paper" and userChose != "scissors":
        userChose = input("Enter choice (rock, paper, scissors): ")

    return (userChose, computerChose)

'''
Game function takes two parameters, the user's choice and the computer's choice, and displays 
who has won the game.
'''
def game(userChose, computerChose):
    print(f"\nYou chose {userChose}, computer chose {computerChose}.\n")
    if userChose == computerChose:
        print(f"It's a tie! Both chose {userChose}.")
    elif userChose == "rock":
        print("You win! Rock beats scissors." if computerChose == "scissors" else "You lose. Paper beats rock.")
    elif userChose == "paper":
        print("You win! Paper beats rock." if computerChose == "rock" else "You lose! Scissors beats paper.")
    elif userChose == "scissors":
        print("You win! Scissors beats paper." if computerChose == "paper" else "You lose! Rock beats scissors.")

'''
main body -  gets choices and plays game until user quits
'''

while True:
    userChose, computerChose = getChoices()
    game(userChose, computerChose)
    if input("Play again? [y]: ") != "y":
        break
