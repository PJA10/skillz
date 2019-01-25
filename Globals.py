def init():
    global prev_game
    global portal_activeness
    global defensive_elf
    global attacking_elves
    global defensive_portals
    global is_enemy_elf_attacking
    global mana_state
    global arrow_next_portal_loc
    global icetrolls_that_target_me
    global dangerous_enemy_portals
    defensive_portals = []
    defensive_elf = None
    attacking_elves = None
    prev_game = 0  # A variable used to save the previous game state
    portal_activeness = {}  # A global dictionary that stores how many turns ago a portal was active. key - portal id
    is_enemy_elf_attacking = False
    mana_state = "save mana"
    arrow_next_portal_loc = None
    icetrolls_that_target_me = {}
    dangerous_enemy_portals = {}