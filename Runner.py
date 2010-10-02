import sys
import subprocess
from os import remove

def runGame(player1, player2, map):
    # todo store these in a sensible place
    statusFileName = 'status.log'
    gameFileName = 't.log'
    status = open(statusFileName, 'w')
    game = open(gameFileName, 'w')
    p = subprocess.Popen(['java', '-jar', 'tools/PlayGame.jar', map, \
                          '200', '200', 'log.txt', \
                          player1, player2], stderr=status, stdout=game)
    p.wait()
    game.close()
    status.close()
    remove(gameFileName)
    status = open(statusFileName, 'r')
    lines = status.readlines()
    status.close()
    remove(statusFileName)
    if lines[len(lines)-1].split()[1] == '1':
        return 1
    else:
        return 2

def usage():
    print("python Runner.py [player1] [player2]")

def main():
    if len(sys.argv) != 3:
        usage()
        return
    p1 = sys.argv[1]
    p2 = sys.argv[2]
    p1wins = 0
    for g in range(1, 100):
        if runGame(p1,p2,'maps/map'+str(g)+'.txt') == 1:
            p1wins += 1
        else:
            print('lost on maps/map'+str(g)+'.txt')
    print('P1 wins ' + str(100*p1wins/100.0) + '%')

main()

    
    
