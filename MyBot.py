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
from Defense import *
import Globals
from Attack import *

ICE = "ice"
LAVA = "lava"


def do_turn(game):
    """

    This function is the main function of the bot which is called every turn.


    :param curr_turn_game_status: the game status, given by the game engine
    :type curr_turn_game_status: Game
    :return: None
    """
    if game.turn == 1:
        Globals.init()
        Globals.prev_game = game
        Globals.is_enemy_elf_attacking_elves = False
        if game.get_all_my_elves:
            Globals.defensive_elf = game.get_all_my_elves()[0]
            Globals.attacking_elfs = game.get_all_my_elves()
            Globals.attacking_elfs.remove(Globals.defensive_elf)
            print "Globals.defensive_elf:", Globals.defensive_elf
            print "Globals.attacking_elfs:", Globals.attacking_elfs

    update_portal_activeness(game)

    # tests(game)
    
    old_do_turn(game)

    # MUST STAY IN THE END OF do_turn():
    Globals.prev_game = copy.deepcopy(game)

    print "threatened portals: ", get_threatened_portals(game)
    print "threatening elves: ", get_threatening_elves(game)


def tests(game):
    """
    print is_targeted_by icetroll(game, game.get_my_living_elves()[0])
    print get_locations(game, game.get_all_elves())
    print get_closest_enemy_elf(game, game.get_my_living_elves()[0])
    print get_closest_enemy_portal(game, game.get_my_living_elves()[0])
    """
    print " ----------start--------- "

    print " ---------predict_next_turn_creatures---------- "
    print predict_next_turn_creatures(game)
    print "predict my lava:\n", predict_next_turn_creatures(game)[0]
    print "predict enemy lava:\n", predict_next_turn_creatures(game)[1]
    print "predict my ice:\n", predict_next_turn_creatures(game)[2]
    print "predict enemy ice:\n", predict_next_turn_creatures(game)[3]

    print "actual my lava:\n", game.get_my_lava_giants()
    print "actual enemy lava:\n", game.get_enemy_lava_giants()
    print "actual my ice:\n",  game.get_my_ice_trolls()
    print "actual enemy ice:\n", game.get_enemy_ice_trolls()

    """
    print " ----------is_in_game_map--------- "
    print "should be True, actual:\n", is_in_game_map(game, Location(0,0))
    print "should be True, actual:\n", is_in_game_map(game, Location(200,300))
    print "should be False, actual:\n", is_in_game_map(game, Location(-10,200))
    print "should be False, actual:\n", is_in_game_map(game, Location(5000000,200))
    print "should be False, actual:\n", is_in_game_map(game, Location(500,-1))
    print "should be False, actual:\n", is_in_game_map(game, Location(500,100000000))
    """

    print " ----------get_circle--------- "
    print "should include (0,10), (-10,0) , (10,0) and (0,-10) actual:\n", get_circle(game, Location(0, 0), 10)

    """
    print " ----------turns_to_travel--------- "
    print "should be 10, actual:\n", turns_to_travel(game, Location(0, 0), Location(1000, 0), 100)
    """

    print " ----------end--------- "


def old_do_turn(game):
    if game.turn == 1:
        prev_turns_elf_locations = get_locations(game, game.get_enemy_living_elves())

    mana = game.default_mana_per_turn + game.get_my_mana()

    handle_elves(game)
    handle_portals(game)

    """
    if Globals.defensive_elf.is_alive():
        create_defensive_portal(game, Globals.defensive_elf, game.get_my_castle())

    live_attacking_elfs = [elf for elf in Globals.attacking_elfs if elf.is_alive()]
    print "live_attacking_elfs", live_attacking_elfs
    for elf in live_attacking_elfs:
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
                func(game, elf, elf.get_location())
            else:
                func(game, elf, 10000)
    """

def normalize(game, elf, destination, func):
    normal = 0

    if func == make_portal:
        if not elf.can_build_portal():
            normal = 0
        else:
            num_of_portals = max(len(get_portals_in_range(game, elf, 3000)), 1)
            d =  abs((1200 - min((elf.distance(game.get_enemy_castle()), elf.distance(game.get_my_castle())))))
            normal = 1.0 / (d*num_of_portals)


    if func == attack_closest_enemy_creature:
        if len(game.get_enemy_creatures()) == 0:
            normal = 0
        else:
            normal = 1.0 / elf.distance(get_closest_enemy_creature(game, elf))

    if func == attack_closest_enemy_portal:
        if len(game.get_enemy_portals()) == 0:
            normal = 0
        else:
            normal = 1.0 / (elf.distance(get_closest_enemy_portal(game, elf)) + 50)

    if func == attack_closest_enemy_elf:
        if len(game.get_enemy_living_elves()) == 0:
            normal = 0
        else:
            normal = 1.0 / elf.distance(closest(game, elf, game.get_enemy_living_elves()))

    print func, normal * 10000
    return normal


def call(game, elf, destination, sliders):
    normal = max(sliders.items(), key=lambda slider: slider[1][0] * normalize(game, elf, destination, slider[1][1]))
    return normal[1][1]


def get_portals_in_range(game, map_object, rng):
    return [portal for portal in game.get_my_portals() if portal.distance(map_object) <= rng]


def handle_elves(game):
    if not game.get_my_living_elves():
        return
    elfs = game.get_my_living_elves()
    elf_def = closest(game, game.get_my_castle(), elfs)
    elfs.remove(elf_def)
    elf_atk = None
    if elfs:
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

    if not port_def or port_def.distance(game.get_my_castle()) > 2000:
        port_atk = port_def
        port_def = None
    if not port_def:

        if not make_portal(game, elf_def, game.get_my_castle().get_location().towards(game.get_enemy_castle(),
                                                                                      game.castle_size * 1.5)):
            if not attack_closest_enemy_portal(game, elf_def, max_distance):
                if not attack_closest_enemy_unit(game, elf_def, max_distance):
                    smart_movement(game, elf_def, game.get_my_castle().get_location().towards(game.get_enemy_castle(),
                                                                                          game.castle_size*1.25))
    else:
        if not attack_closest_enemy_portal(game, elf_def, max_distance):
            if not attack_closest_enemy_unit(game, elf_def, max_distance):
                smart_movement(game, elf_def, game.get_my_castle().get_location().towards(game.get_enemy_castle(),
                                                                                          game.castle_size * 1.25))

    if elf_atk:
        if not port_atk:
            if not make_portal(game, elf_atk,
                               game.get_enemy_castle().get_location().towards(game.get_my_castle(), 1000)):
                if not attack_closest_enemy_portal(game, elf_atk, max_distance):
                    if not attack_closest_enemy_unit(game, elf_atk, max_distance):
                        attack_object(game, elf_atk, game.get_enemy_castle())
        else:
            if not attack_closest_enemy_portal(game, elf_atk, max_distance):
                if not attack_closest_enemy_unit(game, elf_atk, max_distance):
                    attack_object(game, elf_atk, game.get_enemy_castle())

