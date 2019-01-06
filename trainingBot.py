"""
############
trainingBot
############
.. module:: trainingBot
   :platform: Unix, Windows
   :synopsis: A useful module indeed.

.. moduleauthor:: Andrew Carter <andrew@invalid.com>


"""

from elf_kingdom import *


def is_targeted_by_icetroll(game, map_object):
    """

    This function returns a list of all the enemy's icetroll who target a given map object.
    if the returned list is empty then the given map object is safe

    :param map_object: the map object which to check if is targeted bt ice trolls
    :type map_object: MapObject
    :return: return a list of the ice trolls which target obj
    :type: [Creature]
    """
    my_units = game.get_my_creatures() + game.get_my_living_elves()
    icetrolls_that_target_me = [icetroll for icetroll in game.get_enemy_ice_trolls() \
                            if closest(game, icetroll, my_units) == map_object]
    return icetrolls_that_target_me


def closest(game, main_map_object, map_objects_list):
    """

    This function get a main map object and a list of map object and return the closest map object (from the list)
    to the main map object

    :param main_map_object: the map object which to find the closest to
    :type main_map_object: MapObject
    :param map_objects_list: the list of map objects from which to find the closest object to main_map_object
    :type map_objects_list: [MapObject]
    :return: a map object from map_objects_list which is the closest to main_map_object
    :type: MapObject
    """
    if not map_objects_list:
        return None
    else:
        return min(map_objects_list, key = lambda map_object: main_map_object.distance(map_object))


def get_locations(game, map_objects_list):
    """

    This function get a list of map objects and return a list of the map object locations

    :param map_objects_list: a list of objects to get their locations
    :type map_objects_list: [MapObject]
    :return: a list the given list locations
    :type: [Location]
    """

    return [map_object.get_location() for map_object in map_objects_list]


def get_closest_enemy_portal(game, map_object):
    """

    This function return the closest enemy portal to a given map object

    :param map_object: an object on the map in order to find the closest portal to it
    :type map_object: MapObject
    :return: the closest enemy's portal to map_object
    :type: Portal
    """

    return closest(game, map_object,game.get_enemy_portals())



def get_closest_enemy_elf(game, map_object):
    """

    This function return the closest enemy elf to a given map object

    :param map_object: an object on the map in order to find the closest elf to it
    :type map_object: MapObject
    :return: the closest enemy's elf to map_object
    :type: Elf
    """

    return closest(game, map_object, game.get_enemy_living_elves())


def get_closest_enemy_creature(game, map_object):
    """

    This function return the closest enemy creature to a given map object

    :param map_object: an object on the map in order to find the closest creature to it
    :return: the closest enemy's creature to map_object
    :type: Creature
    """

    return closest(game, map_object, game.get_enemy_creatures())


def get_closest_enemy_unit(game, map_object):
    """

    This function return the closest enemy unit(creature + elf) to a given map object

    :param map_object: an object on the map in order to find the closest unit to it
    :return: the closest enemy's unit to map_object
    :type: Creature/Elf
    """
    closest_creature = get_closest_enemy_creature(game, map_object)
    closest_elf = get_closest_enemy_elf(game, map_object)
    return min([closest_elf,closest_creature], key = lambda unit: unit.distance(map_object))


def in_object_range(game, target_map_object, map_objects_list, max_range):
    """

    This function return a list of all the map object from a given list that are in a given range from an target map obj

    :param target_map_object: the target map object which the the range is from
    :param map_objects_list: the list of map object which to search from
    :param max_range: the max distance to which a onj is defined in_range
    :return: list of all the map object from map_objects_list that are in max_range from target_map_object
    :type: [MapObject]
    """

    return [map_object for map_object in map_objects_list if map_object.distance(target_map_object) < max_range]


def summon(game, portal, creature_type_str):
    """

    This function summon a creature from a given portal

    :param portal: the portal to summon from
    :type portal: Portal
    :param creature_type_str: the type of creature to summon in string
    :type creature_type_str: String
    :return: if the summon was succeeded
    :type: Boolean
    """
    summon_dic = {
        "ice": (portal.can_summon_ice_troll, portal.summon_ice_troll),
        "lava": (portal.can_summon_lava_giant, portal.summon_lava_giant)
    }
    if creature_type_str not in summon_dic.keys():
        return False
    else:
        if summon_dic[creature_type_str][0](): # if portal.can_summon_creature
            summon_dic[creature_type_str][1]() # portal.summon_creature
            return True
        else:
            return False


