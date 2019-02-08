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

                if (turns_to_travel(game, elf, portal.get_location().towards(elf, game.elf_attack_range)) <=
                        5 + elf.distance(portal)/game.elf_attack_range):
                    # if the closest enemy elf can get to the given portal in 5 turns or less
                    if not is_targeted_by_my_icetroll(game, elf):
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

                if (turns_to_travel(game, elf, portal.get_location().towards(elf, game.elf_attack_range)) <=
                        5 + elf.distance(portal)/game.elf_attack_range):
                    # if the closest enemy elf can attack the given portal in 5 turns or less
                    if not is_targeted_by_my_icetroll(game, elf):
                        threatening_elves.append(elf)
    return threatening_elves


def ice_troll_defense(game):
    """
    This function will order portals to summon ice trolls based on threatened portals and enemy lava giants
    :return: nothing
    """
    found_portal = False
    threatening_elves = get_threatening_elves(game)
    defensive_ice_trolls = 0
    dangerous_lava_giants_count = 0
    not_summoning_portals = []
    for portal in game.get_my_portals():
        if not portal.is_summoning:
            not_summoning_portals.append(portal)

    for lava_giant in get_dangerous_enemy_lava_giant(game):
        if turns_to_travel(game, lava_giant, game.get_my_castle(), lava_giant.max_speed) < 8:
            dangerous_lava_giants_count += 1

    if threatening_elves:
        for elf in threatening_elves:
            get_closest_my_portal(game, elf).summon_ice_troll()

    for lava_giant in get_dangerous_enemy_lava_giant(game):
        if len(is_targeted_by_my_icetroll(game, lava_giant)) < 1:
            closest(game, game.get_my_castle(), not_summoning_portals).summon_ice_troll()





'''
    for ice_troll in game.get_my_ice_trolls():
        if ice_troll.current_health > ice_troll.max_health / 2.5:
            defensive_ice_trolls += 1
    while game.get_my_mana > 50 and defensive_ice_trolls - 1 < dangerous_lava_giants_count:
        #checkes if has enough mana to summon ice troll
        for portal in game.get_my_portals():
            if portal in not_summoning_portals:
                portal.summon_ice_troll()
                defensive_ice_trolls += 1
'''

'''
    for lava_giant in get_dangerous_enemy_lava_giant(game):
        if get_closest_my_portal(game, lava_giant).can_summon_ice_troll():
            get_closest_my_portal(game, lava_giant).summon_ice_troll()
            summon_with_closest_portal(game, ICE, threatening_elves)

    for lava_giant in game.get_enemy_lava_giants():
        if lava_giant.current_health >= lava_giant.max_health/2 and turns_to_travel(game, lava_giant,
                                                                                    game.get_my_castle()) <= 4:
        # values of lava_giant.max_health/2 and .... 1300 should be adjusted after tests
            game.get_my_castle().get_closest_my_portal(game).summon_ice_troll()
'''












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
