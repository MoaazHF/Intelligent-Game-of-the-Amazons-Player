"""Move ordering for Alpha-Beta. Owner: Mohammed."""






EMPTY,WHITE,BLACK,ARROW=0,1,2,3

DIRECTIONS=[(-1,1),(-1,0),(-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
NEIGHBOURS=[]
for _cell in range(100):
    _r, _c = divmod(_cell,10)
    _nb


def order_moves(state, moves):
    """Return moves sorted with the most promising move first."""
    ...
