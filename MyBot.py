"""
############
MyBot
############
.. module:: MyBot
   :platform: Unix, Windows
   :synopsis: A useful module indeed.

.. moduleauthor:: Andrew Carter <andrew@invalid.com>


"""
from elf_kingdom import *
from trainingBot import *
from Slider import *
ICE = "ice"
LAVA = "lava"

def do_turn(game):
    """

    This function is the main function of the bot which is called every turn.


    :param curr_turn_game_status: the game status, given by the game engine
    :type curr_turn_game_status: Game
    :return: None
    """
    
    #tests(game)
    old_do_turn(game)


def tests(game):
    print is_targeted_by_icetroll(game, game.get_my_living_elves()[0])
    print get_locations(game, game.get_all_elves())
    print get_closest_enemy_elf(game, game.get_my_living_elves()[0])
    print get_closest_enemy_portal(game, game.get_my_living_elves()[0])

def old_do_turn(game):
    if game.turn == 1:
        prev_turns_elf_locations = get_locations(game, game.get_enemy_living_elves())

    mana = game.default_mana_per_turn + game.get_my_mana()

    # handle_elves(game)
    handle_portals(game)
    for elf in game.get_my_living_elves():
        func = call(game, elf, game.get_enemy_castle(), {
            "attack_closest_creature": (1, attack_closest_creature),
            "attack_closest_portal": (1.3, attack_closest_portal),
            "attack_closest_elf": (1.1, attack_closest_elf),
            "make_portal": (1.2, make_portal)
        })
        print func, elf
        if game.turn < 50 and elf == game.get_my_living_elves()[0]:
            elf.move_to(Location(0, 0))
        else:
            if func == make_portal:
                func(game, elf.location, elf)
            else:
                func(game, elf, 10000)


def normalize(game, elf, destination, func):
    normal = 0

    if func == make_portal:
        if not elf.can_build_portal():
            normal = 0
        else:
            normal = 1 / (max(len(get_portals_in_range(game, elf, 3000)), 1) * abs(
                (1200 - min((elf.distance(game.get_enemy_castle()), elf.distance(game.get_my_castle()))))))

    if func == attack_closest_creature:
        if len(game.get_enemy_creatures()) == 0:
            normal = 0
        else:
            normal = 1.0 / elf.distance(get_closest_enemy_creature(game, elf))

    if func == attack_closest_portal:
        if len(game.get_enemy_portals()) == 0:
            normal = 0
        else:
            normal = 1.0 / (elf.distance(get_closest_enemy_portal(game, elf)) + 50)

    if func == attack_closest_elf:
        if len(game.get_enemy_living_elves()) == 0:
            normal = 0
        else:
            normal = 1.0 / elf.distance(closest(game, elf, game.get_enemy_living_elves()))

    print normal * 10000
    return normal


def call(game, elf, destination, sliders):
    normal = max(sliders.items(), key=lambda slider: slider[1][0] * normalize(game, elf, destination, slider[1][1]))
    return normal[1][1]


"""def get_locations(game, objs):
    if objs is []:
        print "You gave me an empty array"
        print "objs", objs
        return False

    locs = []
    for obj in objs:
        locs.append(obj.get_location())
        return locs"""


def is_elf_attacking_portal():
    enemy_elfs = game.get_enemy_living_elves()
    enemy_locs = get_locations(game, enemy_elfs)


def get_portals_in_range(game, map_object, rng):
    return [portal for portal in game.get_my_portals() if portal.distance(map_object) <= rng]


def elf_movment(elf, loc):
    print loc, elf
    elf.move_to(loc)


def make_portal(game, loc, elf):
    # Assumes Mana!

    if elf == None:
        return None
    if elf.get_location() == loc:
        if elf.can_build_portal():
            elf.build_portal()
            return True
        else:
            game.debug("Elf " + str(elf) + " Can't build portal at " + str(loc))
            return False
    else:
        print("Move elf")
        elf_movment(elf, loc)
        return True


def handle_elves(game):
    if len(game.get_my_living_elves()) == 0:
        return
    elfs = game.get_my_living_elves()
    elf_def = closest(game, game.get_my_castle(), elfs)
    elfs.remove(elf_def)
    elf_atk = None
    if len(elfs) != 0:
        elf_atk = elfs[0]

    max_distance = 1300

    ports = game.get_my_portals()
    if len(ports) == 0:
        port_def = None
        port_atk = None
    else:
        port_def = closest(game, game.get_my_castle(), ports)
        ports.remove(port_def)
        port_atk = None
        if len(ports) != 0:
            port_atk = ports[0]

    if port_def == None or port_def.distance(game.get_my_castle()) > 2000:
        port_atk = port_def
        port_def = None
        if not make_portal(game, game.get_my_castle().get_location().towards(game.get_enemy_castle(), 1000), elf_def):
            if not attack_closest_portal(game, elf_def, max_distance):
                attack_closest_enemy(game, elf_def, max_distance)
    else:
        if not attack_closest_portal(game, elf_def, max_distance):
            attack_closest_enemy(game, elf_def, max_distance)

    if elf_atk != None:
        if port_atk == None:
            if not make_portal(game, game.get_enemy_castle().get_location().towards(game.get_my_castle(), 1000),
                               elf_atk):
                if not attack_closest_portal(game, elf_atk, max_distance):
                    attack_closest_enemy(game, elf_atk, max_distance)
        else:
            if not attack_closest_portal(game, elf_atk, max_distance):
                attack_closest_enemy(game, elf_atk, max_distance)



def attack_closest_enemy(game, elf, max_distance):
    target = get_closest_enemy_unit(game, elf)
    if not target:
        return False

    if target.distance(elf) < max_distance:
        if elf.in_attack_range(target):
            elf.attack(target)
            return True
        else:
            elf_movment(elf, target)
            return True



def attack_closest_portal(game, elf, max_distance):
    target = get_closest_enemy_portal(game, elf)
    if not target:
        return False

    if target.distance(elf) < max_distance:
        if elf.in_attack_range(target):
            elf.attack(target)
            return True
        else:
            elf_movment(elf, target)
            return True


def attack_closest_elf(game, elf, max_distance):
    try:
        print "in try"
        target = closest(game, elf, game.get_enemy_living_elves())
        print target
    except:
        return False
    if not target:
        return False

    if target.distance(elf) < max_distance:
        if elf.in_attack_range(target):
            elf.attack(target)
            return True
        else:
            elf_movment(elf, target)
            return True


def attack_closest_creature(game, elf, max_distance):
    target = get_closest_enemy_creature(game, elf)
    if not target:
        return False

    if target.distance(elf) < max_distance:
        if elf.in_attack_range(target):
            elf.attack(target)
            return True
        else:
            elf_movment(elf, target)
            return True


def handle_portals(game):
    ports = game.get_my_portals()
    if len(ports) == 0:
        return
    port_def = closest(game, game.get_my_castle(), ports)
    print "port_def", port_def
    ports.remove(port_def)
    port_atk = None
    if len(ports) != 0:
        port_atk = ports[0]

    if port_def.distance(game.get_my_castle()) > 2000:
        port_atk = port_def
        port_def = None
    if port_def != None:
        if in_object_range(game, game.get_my_castle(), game.get_enemy_creatures() + game.get_enemy_living_elves(), 3000):
            print("in if in handle_portals")
            if (game.get_my_ice_trolls() is None or len(game.get_my_ice_trolls()) < 3) or game.get_my_mana() > 200:
                summon(game, port_def, ICE)
    if port_atk != None:
        summon(game, port_atk, LAVA)
