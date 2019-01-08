def init():
    global prev_game
    global portal_activeness
    global defensive_elf
    global attacking_elfs
    global defensive_portals
    defensive_portals = []
    defensive_elf = None
    attacking_elfs = None
    prev_game = 0  # A variable used to save the previous game state
    portal_activeness = {}  # A global dictionary that stores how many turns ago a portal was active. key - portal id
