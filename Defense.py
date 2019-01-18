from elf_kingdom import *
from trainingBot import *
import Globals
from Slider import *


def enemy_elf_threatening_portal(game, portal):
    """
    This function checks if one of the enemy elves threatening the given portal. It checks if one of the enemy elves can
    get to the given portal in 5 turns or less + that he is not targeted by close(to the elf) ally ice trolls
    :param portal: an ally portal in order to check if it's in danger
    :return: if one of the enemy elves is a threat to the given portal
    :type: bool
    """

    if not game.get_enemy_living_elves()[0]:
        for elf in game.get_enemy_living_elves:
            if turns_to_travel(game, elf, portal, game.elf_max_speed()) <= 6:
            # if the closest enemy elf can get to the given portal in 6 turns or less
                for ice_troll in game.get_my_ice_trolls():
                    if elf.location().distance(ice_troll) >= 800:
                        return True

    return False


def should_summon_ice_troll(game):
    """
    This function checks if we should summon ice trolls in order to defend our portals/castle and return true if we
    should
    :return: if we should summon ice trolls to defend
    :type: bool
    """

    for portal in game.get_my_portals():
        if enemy_elf_threatening_portal(game, portal):
            return True

    for lava_giant in game.get_enemy_lava_giants():
        if lava_giant.current_health >= lava_giant.max_health/2 and game.get_my_castle().distance(lava_giant) <= 1800:
            #values of lava_giant.max_health/2 and .... 1300 should be adjusted after tests
            return True

    return False



'''
def attacked_portals(game):
    """
    This function checks if enemy elf is attacking one of our portals
    :param : none
    :return: a list of the portals that was attacked last turn
    :type: [portal]
    """
    attacked_portals = []
    prev_game = Globals.prev_game
    for portal in game.get_my_portals():
        if(prev_game.portal.current_health >= portal.current_health):
            attacked_portals.append(portal)
    return attacked_portals
'''


'''
    """
def which_enemy_elves_attacking_our_portals():
    """
    #This function return a list of the elves that attacking one of our portals
    #:param : none
    #:return: a list of the elves that attacking our portals 
    #:type: [elf]
    """
    attacking_elves = []
    prev_game = Globals.prev_game
    attacked_portals = attacked_portals()
    for elf
    """
'''
