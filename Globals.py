def init():
    global prev_game
    global portal_activeness
    prev_game = 0  # A variable used to save the previous game state
    portal_activeness = {}  # A global dictionary that stores how many turns ago a portal was active. key - portal id