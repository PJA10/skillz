"""

"""

from Attack import *


def full_strategy(game):
    """

    :param game:
    :return:
    """

    build_base(game, Globals.defensive_elf)
    arrow_strategy(game, Globals.attacking_elves)


def build_base(game, elf):
    num_of_my_portals = len(game.get_my_portals())
    number_of_my_fountains = len(game.get_my_fountains())
    if math.ceil(num_of_my_portals/5) > number_of_my_fountains:
        full_build_fountain(game, elf)
    else:
        full_build_portal(game, elf, game.castle_size + 2* game.mana_fountain_size + game.portal_size + 20)


def full_build_fountain(game, elf):
    points = get_circle(game, game.get_my_castle().get_location(), game.castle_size + game.mana_fountain_size + 10, 5)
    for point in points:
        if not disturbing_buildings(game, point, game.mana_fountain_size):
            if game.mana_fountain_size <= point.col <= game.cols - game.mana_fountain_size and\
                    game.mana_fountain_size <= point.row <= game.rows - game.mana_fountain_size:
                build(game, elf, MANA_FOUNTAIN, point)
                return


def full_build_portal(game, elf, radius_from_castle, second_run=False):
    points = get_circle(game, game.get_my_castle().get_location(), radius_from_castle, 5)
    for point in points:
        if not disturbing_buildings(game, point, game.portal_size):
            if game.portal_size <= point.col <= game.cols - game.portal_size and \
                    game.portal_size <= point.row <= game.rows - game.portal_size:
                build(game, elf, PORTAL, point)
                return
    if not full_build_portal:
        return full_build_portal(game, elf, radius_from_castle + game.portal_size * 2 + 10, second_run=True)


