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
from Defense import *
import Globals
from Attack import *
import time
from rush_v1 import *

ICE = "ice"
LAVA = "lava"


def do_turn(game):
    """

    This function is the main function of the bot which is called every turn.


    :param curr_turn_game_status: the game status, given by the game engine
    :type curr_turn_game_status: Game
    :return: None
    """
    start_time = time.time()
    if game.turn == 1:
        Globals.init()
        Globals.prev_game = game
        Globals.is_enemy_elf_attacking_elves = False
        if len(game.get_enemy_ice_trolls()) > 30:
            Globals.Labyrinth = True
        if len(game.get_enemy_portals()) == 5 and not game.get_all_enemy_elves():
           Globals.mazgan = True
        if game.get_all_my_elves():
            Globals.defensive_elf = game.get_all_my_elves()[0]
            Globals.attacking_elfs = game.get_all_my_elves()
            Globals.attacking_elfs.remove(Globals.defensive_elf)
            # print "Globals.defensive_elf:", Globals.defensive_elf
            # print "Globals.attacking_elfs:", Globals.attacking_elfs
    
    update_enemy_ice_trolls_targets(game)
    update_dangerous_enemy_portals(game)
    # tests(game)

    if game.turn < 8 and not game.get_my_mana_fountains():
        elves = copy.deepcopy(game.get_my_living_elves())
        if elves and len(elves) > 1:
            loc = get_new_mana_fountain_loc(game)
            closest_elf_to_loc = closest(game, loc, elves)
            build(game, closest_elf_to_loc, MANA_FOUNTAIN, get_new_mana_fountain_loc(game))
            print "elf %s building MANA_FOUNTAIN at %s" % (closest_elf_to_loc, get_new_mana_fountain_loc(game))
            elves.remove(closest_elf_to_loc)
        choose_strategy(game, elves)
    else:
        choose_strategy(game, game.get_my_living_elves())
    # rush_strat(game, game.get_my_living_elves())

    # old_do_turn(game)
    # MUST STAY IN THE END OF do_turn():
    Globals.prev_game = copy.deepcopy(game)

    # print "threatened portals: ", get_threatened_portals(game)
    # print "threatening elves: ", get_threatening_elves(game)
    print "--- %s mseconds ---" % (time.time()*1000 - start_time*1000)  # second to ms *1000
    print "--- %s mseconds get_time_remaining ---" % (game.get_time_remaining())  # second to ms *1000


def update_enemy_ice_trolls_targets(game):
    """
    """
    
    Globals.who_target_me_dic = {}
    Globals.who_do_i_target = {}
    
    for enemy_ice_troll in game.get_enemy_ice_trolls():
        target = closest(game, enemy_ice_troll, game.get_my_creatures() + game.get_my_living_elves())
        if target:
            if not Globals.who_target_me_dic.get(target):
                Globals.who_target_me_dic[target] = [enemy_ice_troll]
            else:
                Globals.who_target_me_dic[target].append(enemy_ice_troll)
            Globals.who_do_i_target[enemy_ice_troll] = target
                
    for my_ice_troll in game.get_my_ice_trolls():
        target = closest(game, my_ice_troll, game.get_enemy_creatures() + game.get_enemy_living_elves())
        if target:
            if not Globals.who_target_me_dic.get(target):
                Globals.who_target_me_dic[target] = [my_ice_troll]
            else:
                Globals.who_target_me_dic[target].append(my_ice_troll)
            Globals.who_do_i_target[my_ice_troll] = target


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

def choose_strategy(game, elves):
    """
    This function is the main choosing strategy function
    she determine that by try to determine_enemy_strategy 
    and looking on the game status
    
    :param: game
    :type: void
    
    """
    
    
    
    
    if Globals.Labyrinth:
        Counter_Labyrinth(game)
    elif Globals.mazgan:
        Counter_mazgan(game)
    
    else:
        arrow_strategy(game, elves)







def determine_enemy_strategy(game):
    """
    this function try to determine_what_strategy_is_an_enemy_using
    
    :param: game
    :return: the name of the strategy
    :type: string
    
    possible returns:
    "rush"
    "controling the center"
    "bunker"
    
    """
    
    
def Counter_mazgan(game):
    
    
    for portal in game.get_my_portals():
        if not game.get_my_tornadoes():
            summon(game, portal, TORNADO)
        if not portal.is_summoning:
            summon(game, portal, ICE)
    for elf in game.get_my_living_elves():
        if game.get_enemy_lava_giants():
            attack_object(game, elf, get_closest_enemy_creature(game, elf))
        else:
            attack_object(game, elf, game.get_enemy_castle())
    
    
def Counter_Labyrinth(game):
    
    for elf in game.get_my_living_elves():
        if elf.in_attack_range(game.get_enemy_castle()):
            attack_object(game,elf,game.get_enemy_castle())
        elif game.get_enemy_ice_trolls():
            if elf.can_cast_invisibility() and not elf.invisible:
                elf.cast_invisibility()
            else:
                elf.move_to(game.get_enemy_castle())
        else: 
                elf.move_to(game.get_enemy_castle())
