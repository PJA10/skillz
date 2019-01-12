# -*- coding: utf-8 -*-

from elf_kingdom import *
from trainingBot import *
from MyBot import *
from Slider import *

def Enemy_elf_nearby(game,portal):
    """

    This function checks if one of the enemy elves threatening the given portal. It checks if one of the enemy elves can
    get to the given portal in 5 turns or less + that he is not targeted by ally ice trolls

    :param portal: an ally portal in order to check if it's in danger
    :return: if one of the enemy elves is a threat to the given portal
    :type: bool
    """
        if portal.get_location().distance(get_closest_enemy_elf().get_location()) <= : #if the closest enemy elf can get to the given po
