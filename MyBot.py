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
import time

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
        if game.get_all_my_elves():
            Globals.defensive_elf = game.get_all_my_elves()[0]
            Globals.attacking_elfs = game.get_all_my_elves()
            Globals.attacking_elfs.remove(Globals.defensive_elf)
            # print "Globals.defensive_elf:", Globals.defensive_elf
            # print "Globals.attacking_elfs:", Globals.attacking_elfs
    '''
    if game.turn < 9:
        elf = game.get_my_living_elves()[0]
        elf2 = game.get_my_living_elves()[1]
        if elf.distance(Location(0,0)) < elf2.distance(Location(0,0)):
            target = Location(0,0)
            target2 = Location(3500, 5800)
        else:
            target = Location(3500, 5800)
            target2 = Location(0,0)
            
        if game.turn == 8:
            if elf.can_build_mana_fountain():
                elf.build_mana_fountain()
            if elf2.can_build_mana_fountain():
                elf2.build_mana_fountain()
        else:
            elf.move_to(elf.get_location().towards(target, game.elf_max_speed))
            elf2.move_to(elf2.get_location().towards(target2, game.elf_max_speed))
        Globals.prev_game = copy.deepcopy(game)
        return
    '''
    Globals.icetrolls_that_target_me = {}
    update_dangerous_enemy_portals(game)
    # tests(game)
    print game.mana_fountain_mana_per_turn
    
    # old_do_turn(game)
    arrow_strategy(game)
    # MUST STAY IN THE END OF do_turn():
    Globals.prev_game = copy.deepcopy(game)

    # print "threatened portals: ", get_threatened_portals(game)
    # print "threatening elves: ", get_threatening_elves(game)
    print "--- %s seconds ---" % (time.time()*1000 - start_time*1000)  # second to ms *1000


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

