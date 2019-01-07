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
import Globals
import math
import copy 


def is_targeted_by_icetroll(game, map_object):
    """

    This function returns a list of all the enemy's icetroll who target a given map object.
    if the returned list is empty then the given map object is safe

    :param map_object: the map object which to check if is targeted bt ice trolls
    :type map_object: MapObject
    :return: return a list of the ice trolls which target obj
    :type: [Creature]
    """

    icetrolls_that_target_me = [icetroll for icetroll in game.get_enemy_ice_trolls()
                                if get_closest_friendly_unit(game, icetroll) == map_object]
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

    if not closest_creature and not closest_elf:
        return None

    if not closest_creature:
        return closest_elf

    if not closest_elf:
        return closest_creature

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


def create_defensive_portal(game, defensive_elf, castle):
    """

    This function tells a given elf to place a portal between a given castle and all active portals +- a radius


    :param defensive_elf: the elf that is meant to create the defensive portal
    :type Elf:
    :param castle: the castle that the given portal is meant to defend
    :type Castle:
    :return: returns False if no portals need to be created
    :type: Boolean
    """

    active_portals = []
    for port in game.get_enemy_portals():
        turns_to_castle = castle.distance(port) / game.lava_giant_max_speed
        life_expectancy_of_lava_giant = game.lava_giant_max_health / game.lava_giant_suffocation_per_turn
        if Globals.portal_activeness[port.id] < life_expectancy_of_lava_giant - turns_to_castle: #the closer a portal is to our castle the more aware we want to be
            active_portals.append(port)

    minimum_distance = game.castle_size + game.portal_size + 50
    defense_positions = []
    for port in active_portals:
        defense_positions.append(castle.towards(port), minimum_distance)


def update_portal_activeness(game):
    """

    a function that updates portal_activeness
    portal_activeness: A global dictionary that stores how many turns ago a portal was active. key - portal id.

    """

    enemy_portals = game.get_enemy_portals()
    for port in enemy_portals:
        if port.currently_summoning or port.id not in Globals.portal_activeness:
            Globals.portal_activeness[port.id] = 0
        else:
            Globals.portal_activeness[port.id] += 1


def attack(game, elf, map_object):
    """

    This function attack with an elf a map object
    if the map object is too far the elf will move towards the map object
    WILL CRASH IF GET NONE

    :param elf: the elf to attck with
    :param map_object: the map_object to attack
    """

    if not elf or not map_object:
        print "attack() got None"

    if elf.in_attack_range(map_object):
        elf.attack(map_object)
    else:
        elf.move_to(map_object)


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


def make_portal(game, elf, loc):
    """

    This function make a portal with a given elf at a specific location
    If the elf isn't at this position the elf will move towards the location

    :param elf: the elf to build a portal with
    :param loc: the location to build a portal at
    :type loc: Location
    :return: if the an action has been made with the elf, can be movement or building portal
    :type: Boolean
    """

    if not elf:
        return None

    if elf.get_location() == loc:
        if elf.can_build_portal():
            elf.build_portal()
            return True
        else:
            print ("Elf " + str(elf) + " Can't build portal at " + str(loc))
            return False
    else:
        elf_movement(game, elf, loc)
        return True


def elf_movement(game, elf, map_object):
    """

    This function takes a elf and moves is towards a spisific map_object

    :param elf: the elf to move towards map_object
    :param map_object: the map object to move to
    :return: if the an action has been made with the elf
    :type: Boolean
    """

    # print "elf: %s moves towards %s" % (elf, map_object)
    elf.move_to(map_object)
    return True


def turns_to_travel(game, map_object, destination, max_speed):
    """

    This function calculate the amount of turns a given path will take with an object with a given speed

    :param map_object: the start point of the travel
    :param destination: the destination of the travel
    :param max_speed: the speed of the object traveling
    :return: the amount of turns needed to complete the travel
    :type: int
    """

    distance = map_object.distance(destination)
    number_of_turns = math.ceil(distance/max_speed)
    return number_of_turns


def smart_movement(game, elf, destination):
    """



    :param game:
    :param elf:
    :param destination:
    :type destination: MapObject
    :return:
    """
    """
    circle_points = get_circle(game, elf.get_location(), elf.max_speed)
    circle_points = [point for point in circle_points if is_in_game_map(game, point)]"""
    pass


def get_closest_friendly_unit(game, map_object):
    """

    This function return the closest friendly unit(creature + elf) to a given map object

    :param map_object: an object on the map in order to find the closest unit to it
    :return: the closest enemy's unit to map_object
    :type: Creature/Elf
    """

    closest_creature = get_closest_friendly_creature(game, map_object)
    closest_elf = get_closest_friendly_creature(game, map_object)

    if not closest_creature and not closest_elf:
        return None

    if not closest_creature:
        return closest_elf

    if not closest_elf:
        return closest_creature

    return min([closest_elf,closest_creature], key=lambda unit: unit.distance(map_object))


def get_closest_friendly_elf(game, map_object):
    """

    This function return the closest friendly elf to a given map object

    :param map_object: an object on the map in order to find the closest elf to it
    :type map_object: MapObject
    :return: the closest enemy's elf to map_object
    :type: Elf
    """

    return closest(game, map_object, game.get_my_living_elves())


def get_closest_friendly_creature(game, map_object):
    """

    This function return the closest friendly creature to a given map object

    :param map_object: an object on the map in order to find the closest creature to it
    :return: the closest enemy's creature to map_object
    :type: Creature
    """

    return closest(game, map_object, game.get_my_creatures())


def get_circle(game, circle_location, radius):
    """

    This function create a circle around a given location in a given radius

    :param game:
    :param circle_location: The location of the center of the circle
    :type circle_location: Location
    :param radius: the length of the radius
    :return: a list of point on a circle with circle_location as a the center and with radius equals radius
    :type: [Location]
    """

    circle_points = []
    for angle in range(0, 360, 15):
        angle_in_radius = math.radians(angle)
        x_part = radius * math.cos(angle_in_radius)
        y_part = radius * math.sin(angle_in_radius)
        pos = Location(x_part, y_part)
        circle_points.append(circle_location.add(pos))
    return circle_points


def is_in_game_map(game, location):
    """

    This function check if a given location is inside the game map

    :param game:
    :param location: the location to check
    :return: if *location* is inside the game map
    """

    if location.row > game.rows or location.row < 0:
        return False
    if location.col > game.cols or location.col < 0:
        return False

    return True


def predict_next_turn_creatures(game):
    """

    This function predict the locations of all creatures for next turn

    :param game:
    :return: the list of my next turn lava giants, the list of the enemy's next turn lava giants
        the list of my next turn trolls, the list of the enemy's next turn trolls
    :type: ([LavaGiants], [LavaGiants], [IceTroll], [IceTroll])
    """
    
    next_turn_my_lava_giant_list, next_turn_enemy_lava_giant_list = predict_next_turn_lava_giant(game)
    next_turn_my_icetrolls_list, next_turn_enemy_icetrolls_list = predict_next_turn_ice_trolls(game)

    return next_turn_my_lava_giant_list, next_turn_enemy_lava_giant_list,\
            next_turn_my_icetrolls_list, next_turn_enemy_icetrolls_list


def predict_next_turn_ice_trolls(game):
    """

    This function predict the locations of the ice trolls for next turn

    :param game:
    :return: the list of my next turn trolls, the list of the enemy's next turn trolls
    :type: ([IceTroll], [IceTroll])
    """

    next_turn_my_icetroll_list = []

    for my_icetroll in game.get_my_ice_trolls():
        next_turn_my_icetroll = copy.deepcopy(my_icetroll)
        target = get_closest_enemy_unit(game, my_icetroll)
        if my_icetroll.distance(target) > my_icetroll.attack_range:
            next_turn_my_icetroll.location = my_icetroll.get_location().towards(target, game.ice_troll_max_speed)
        next_turn_my_icetroll_list.append(next_turn_my_icetroll)

    next_turn_enemy_icetroll_list = []

    for enemy_icetroll in game.get_enemy_ice_trolls():
        next_turn_enemy_icetroll = copy.deepcopy(enemy_icetroll)
        target = get_closest_friendly_unit(game, enemy_icetroll)
        if enemy_icetroll.distance(target) > enemy_icetroll.attack_range:
            next_turn_enemy_icetroll.location = enemy_icetroll.get_location().towards(target, game.ice_troll_max_speed)
        next_turn_enemy_icetroll_list.append(next_turn_enemy_icetroll)

    return next_turn_my_icetroll_list, next_turn_enemy_icetroll_list


def predict_next_turn_lava_giant(game):
    """

    This function predict the locations of the lava giants for next turn

    :param game:
    :return: the list of my next turn lava giants, the list of the enemy's next turn lava giants
    :type: ([LavaGiants], [LavaGiants])
    """

    next_turn_my_lava_giant_list = []
    target = game.get_enemy_castle()

    for my_lava_giant in game.get_my_lava_giants():
        next_turn_my_lava_giant = copy.deepcopy(my_lava_giant)
        if my_lava_giant.distance(target) > my_lava_giant.attack_range:
            next_turn_my_lava_giant.location = my_lava_giant.get_location().towards(target, game.lava_giant_max_speed)
        next_turn_my_lava_giant_list.append(next_turn_my_lava_giant)
    
    next_turn_enemy_lava_giant_list = []
    target = game.get_my_castle()

    for enemy_lava_giant in game.get_enemy_lava_giants():
        next_turn_enemy_lava_gian = copy.deepcopy(enemy_lava_giant)
        if enemy_lava_giant.distance(target) > enemy_lava_giant.attack_range:
            next_turn_enemy_lava_gian.location = enemy_lava_giant.get_location().towards(target, game.lava_giant_max_speed)
        next_turn_enemy_lava_giant_list.append(next_turn_enemy_lava_gian)

    return next_turn_my_lava_giant_list, next_turn_enemy_lava_giant_list
