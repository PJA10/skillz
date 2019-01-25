from elf_kingdom import *
from trainingBot import *
import Globals
from Slider import *


def get_threatened_portals(game):
    """
    This function checks if one of the enemy elves threatening the given portal. It checks if one of the enemy elves can
    get to the given portal in 7 turns or less + that he is not targeted by close(to the elf) ally ice trolls
    :return: all the threatened portals
    :type: list
    """
    threatened_portals = []
    if game.get_enemy_living_elves():
        for portal in game.get_my_portals():
            for elf in game.get_enemy_living_elves():
                if (turns_to_travel(game, elf, portal.get_location().towards(elf, game.elf_attack_range),
                                                game.elf_max_speed) <= 5 + elf.distance(portal)/game.elf_attack_range):
                    #if the closest enemy elf can get to the given portal in 5 turns or less
                    for ice_troll in game.get_my_ice_trolls():
                        if get_closest_enemy_unit(game, ice_troll) == elf and elf.distance(ice_troll) >= 400:
                            if portal not in threatened_portals:
                                threatened_portals.append(portal)

    return threatened_portals


def get_threatening_elves(game):
    """
    This function checks if one of the enemy elves threatening the given portal. It checks if one of the enemy elves can
    get to the given portal in 7 turns or less + that he is not targeted by close(to the elf) ally ice trolls
    :return: the enemy elves that threatening our portals
    :type: list
    """
    threatening_elves = []
    if game.get_enemy_living_elves():
        for portal in game.get_my_portals():
            for elf in game.get_enemy_living_elves():
                if (turns_to_travel(game, elf, portal.get_location().towards(elf, game.elf_attack_range),
                                                game.elf_max_speed) <= 5 + elf.distance(portal)/game.elf_attack_range):
                    threatening_elves.append(elf)
                    for ice_troll in game.get_my_ice_trolls():
                        if (get_closest_enemy_unit(game, ice_troll).unique_id ==
                        elf.unique_id and elf.distance(ice_troll)<= 400):
                            if elf in threatening_elves:
                                threatening_elves.remove(elf)
    return threatening_elves


def ice_troll_defense(game):
    """
    This function will order portals to summon ice trolls based on threatened portals and enemy lava giants
    :return: nothing
    """

    threatening_elves = get_threatening_elves(game)
    if threatening_elves:
        for elf in threatening_elves:
            if get_closest_my_portal(game, elf).can_summon_ice_troll():
                get_closest_my_portal(game, elf).summon_ice_troll()

    for lava_giant in get_dangerous_enemy_lava_giant(game):
        if get_closest_my_portal(game, lava_giant).can_summon_ice_troll():
            get_closest_my_portal(game, lava_giant).summon_ice_troll()



def attacks_close_portals_defense(game):
    """


    This function checks if an enemy elf starts creating a portal close to us,
    if he is elf and ice troll will be send to attack him and the portal
    :return: nothing
    """
    building_close_elf = []
    if game.get_enemy_living_elves():
        for elf in game.get_enemy_living_elves():
            if elf.is_building and game.get_my_castle().distance(elf) <= 2000:
                if get_closest_my_portal(game, elf).can_summon_ice_troll():
                    get_closest_my_portal(game, elf).summon_ice_troll()
            if game.get_my_living_elves():
                if get_closest_friendly_elf(game, elf).distance(elf) <= 1000:
                    attack_object(game, get_closest_friendly_elf(game, elf), elf)
    return building_close_elf






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
