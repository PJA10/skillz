def init():
    global prev_game
    global portal_activeness
    global defensive_elf
    global attacking_elves
    global defensive_portals
    global is_enemy_elf_attacking
    global mana_state
    global arrow_next_portal_loc
    global who_target_me_dic
    global possible_dangerous_enemy_portals
    global who_do_i_target
    defensive_portals = []
    defensive_elf = None
    attacking_elves = None
    prev_game = 0  # A variable used to save the previous game state
    portal_activeness = {}  # A global dictionary that stores how many turns ago a portal was active. key - portal id
    is_enemy_elf_attacking = False
    mana_state = "save mana"
    arrow_next_portal_loc = None
    who_target_me_dic = {}
    who_do_i_target = {}
    possible_dangerous_enemy_portals = {}