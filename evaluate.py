from collections import deque
from game_state import EMPTY, WHITE, BLACK, ARROW, SIZE

Directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

# THESE ARE ALL THE POSSIBLE DIRECTIONS WHICH WILL BE USED TO MODIFY THE COORDINATES




def _find_amazons(cells, color):
    Positions = []
    size = SIZE  # the board is a flat list of 100 cells: cell = row * 10 + col
    for r in range(size):
        for c in range(size):
            if cells[r * size + c] == color:
                Positions.append((r, c))
    return Positions




# here we first defined an empty list and determined the size of the board 
# using the len() function then we looped through the whole board to determine 
# where each amazon is







def _mobility_for_color(cells, amazon_positions):
    size = SIZE  # the board is a flat list of 100 cells: cell = row * 10 + col
    moves_count = 0
    for start_r, start_c in amazon_positions:
        for direction_r, direction_c in Directions:
            row = start_r + direction_r
            column = start_c + direction_c

            while  0 <= row < size and 0 <= column < size and cells[row * size + column] == EMPTY:
                moves_count = moves_count + 1
                row += direction_r
                column += direction_c
    return moves_count



# In this function  we calculate the mobility of whether the opponent or the player we start by defining the size
# and then cearte a placeholder for the moves count, mobility calculates the total number of available steps for the player
# we then loop through the start posititons of each amazon and then we add all the legal directions tot he start coordinates
# then using a while loop we check if the new coordinates are free (EMPTY) and in the border of the board, if so then we move the amazon
# and we add 1 to the moves_count and we start all over
  






INF = 999999   # CONSTANT FOR UNVISITED SQUARES


def _queen_bfs_distances(cells, amazon_positions):

    size = SIZE  # the board is a flat list of 100 cells: cell = row * 10 + col
    dist = [[INF for _ in range(size)] for _ in range(size)]

    queue = deque()

    for row, column in amazon_positions:
        dist[row][column] = 0
        queue.append((row, column))

    while queue:

        current_r, current_c = queue.popleft()
        next_distance = dist[current_r][current_c] + 1
        
        for direction_r, direction_c in Directions:
            row = current_r + direction_r
            column = current_c + direction_c

            while 0 <= row < size and 0 <= column < size and cells[row * size + column] == EMPTY:
                
                if dist[row][column] == INF:
                    dist[row][column] = next_distance
                    queue.append((row, column))
                row += direction_r 
                column += direction_c

    return dist



# In this function our main purpose is to declare who -in terms of each amazon corresponding to their player- can reach the specified 
# square in the least amount of moves, in simple terms if the opponenet can reach it faster then we declare this move as bad and vice versa
# we do so b first creating a 2D distance list and using the deque library to create a queue for the moves then we create a 
# while loop that checks if there are any orders in the queue if there is any then we start by defining the current position and
# then defining the next distance then we create the move using the for loop and we come up with the new coordinates
# then again we checl if its EMPTY and inside the board borders if so then we check whether the cell is visited or no 
# and we evaluate the row and column then we return the





W1 = 1.0   # weight of territory (experiments.py changes these to compare weights)
W2 = 0.2   # weight of mobility


def evaluate(state, color):

    if color == WHITE:
        opponent = BLACK
    else: opponent = WHITE

    cells = state.cells
    size = SIZE  # the board is a flat list of 100 cells: cell = row * 10 + col

    my_amazons = _find_amazons(cells, color)
    opp_amazons = _find_amazons(cells, opponent)
    my_mobility = _mobility_for_color(cells, my_amazons)
    opp_mobility = _mobility_for_color(cells, opp_amazons)
    TOTAL_mobility = my_mobility - opp_mobility

    my_dist = _queen_bfs_distances(cells, my_amazons)
    opp_dist = _queen_bfs_distances(cells, opp_amazons)
    territory = 0
    for row in range(size):
        for column in range(size):
            if cells[row * size + column] == EMPTY:
                if my_dist[row][column] < opp_dist[row][column]:
                    territory = territory + 1
                elif opp_dist[row][column] < my_dist[row][column]:
                    territory = territory -1

    return W1 * territory + W2 * TOTAL_mobility
