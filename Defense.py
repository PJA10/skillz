
from elf_kingdom import *
from trainingBot import *
from MyBot import *
import Globals
from Slider import *


def enemy_elf_nearby(game,portal):
    """

    This function checks if one of the enemy elves threatening the given portal. It checks if one of the enemy elves can
    get to the given portal in 5 turns or less + that he is not targeted by close(to the elf) ally ice trolls

    :param portal: an ally portal in order to check if it's in danger
    :return: if one of the enemy elves is a threat to the given portal
    :type: bool
    """

    if not game.get_enemy_living_elves()[0]:
        if turns_to_travel(game, game.get_enemy_living_elves(), portal, game.elf_max_speed()) <= 5:
        # if the closest enemy elf can get to the given portal
            for ice_troll in game.get_enemy_ice_trolls():
                    if game.get_enemy_living_elves()[0].location().distance(ice_troll) >= 600:
                        return True

    if not game.get_enemy_living_elves():
        if not game.get_enemy_living_elves()[1]:
            if turns_to_travel(game, game.get_enemy_living_elves(), portal, game.elf_max_speed()) <= 5:
             # if the closest enemy elf can get to the given portal
                for ice_troll in game.get_enemy_ice_trolls():
                    if game.get_enemy_living_elves()[1].location().distance(ice_troll) >= 600:
                        return True

    return False


#def enemy_attacking_portal(game):
    """

    This function checks if enemy elf is attacking one of our portals

    :param : none
    :return: if one of the enemy elves is a attacking one of our portals
    :type: [portal]
    """
#   prev_game = Globals.prev_game
#    for portal in game.get_my_portals():
#        if(prev_game.portal.current_health > portal.current_health):
