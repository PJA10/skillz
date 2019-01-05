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
                            if closest(icetroll, my_units) == map_object]
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
        return min(map_objects_list, key = lambda map_object: main_map_object.distance(map_objects_list))


def get_locations(game, map_objects_list):
    """

    This function get a list of map objects and return a list of the map object locations

    :param map_objects_list: a list of objects to get their locations
    :type map_objects_list: [MapObject]
    :return: a list the given list locations
    :type: [Location]
    """

    return [map_object.get_location() for map_object in map_objects_list]


def closest_portal(game, map_object):
    """

    This function get a map object and return the close portal to it

     :param game, map_object: an object on the map in order to find the closest portal to it
     :type map_object: MapObject map_object
     :return: the closest portal to map_object
     :type: [Location]
    """

    return closest(game, map_object,game.get_enemy_portals())



def closest_elf(game,map_object):
    """

    This function return the closest elf to the given map object

    :param game, map_object: an object on the map in order to find the closest elf to it
    :type map object: MapObject map_object
    :return: the closest elf to map_object
    :type: [location]
    """

    return closest(game, map_object, game.get_enemy_living_elves())
