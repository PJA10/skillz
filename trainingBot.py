# coding=utf-8
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
from collections import *
import time

RISK_AMOUNT = 1
ICE = "ice"
LAVA = "lava"
MANA_FOUNTAIN = "mana fountain"
PORTAL = "portal"


def is_targeted_by_enemy_icetroll(game, map_object):
    """

    This function returns a list of all the enemy's icetroll who target a given map object.
    if the returned list is empty then the given map object is safe

    :param map_object: the map object which to check if is targeted bt ice trolls
    :type map_object: MapObject
    :return: return a list of the ice trolls which target obj
    :type: [IceTroll]
    """

    if map_object in Globals.icetrolls_that_target_me:
        return Globals.icetrolls_that_target_me[map_object]

    icetrolls_that_target_map_object = [icetroll for icetroll in game.get_enemy_ice_trolls()
                                if get_closest_my_unit(game, icetroll) == map_object]
    Globals.icetrolls_that_target_me[map_object] = icetrolls_that_target_map_object
    return icetrolls_that_target_map_object


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

    enemy_units = get_player_units(game, game.get_enemy())
    return closest(game, map_object, enemy_units)


def get_closest_enemy_portal(game, map_object):
    """

    This function return the closest enemy portal to a given map object

    :param map_object: an object on the map in order to find the closest portal to it
    :return: the closest enemy's portal to map_object
    :type: Portal
    """

    return closest(game, map_object, game.get_enemy_portals())


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
    :type defensive_elf: Elf
    :param castle: the castle that the given portal is meant to defend
    :type castle: Castle
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
    defense_positions = [castle.get_location().towards(port, minimum_distance) for port in active_portals]

    for pos in defense_positions:
        for portal in game.get_my_portals():
            if portal.distance(pos) < game.portal_size * 2:
                defense_positions.remove(pos)
                continue

    """find a fix for this"""
    for pos in defense_positions:
        for pos2 in defense_positions:
            if pos == pos2:
                continue
            if pos.distance(pos2) < game.portal_size * 2:
                defense_positions.append(pos.towards(pos2, pos.distance(pos2)/2))
                defense_positions.remove(pos)
                defense_positions.remove(pos2)

    if not defense_positions:
        return False

    defense_positions.sort(key=lambda pos: pos.distance(defensive_elf))
    if defensive_elf.location.equals(defense_positions[0]):
        if defensive_elf.can_build_portal():
            defensive_elf.build_portal()
        else:
            return False
    else:
        defensive_elf.move_to(defense_positions[0])
    return True


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


def attack_object(game, elf, map_object):
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
        smart_movement(game, elf, map_object)


def aggressive_attack_object(game, elf, map_object):
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


def handle_defensive_elf(game, elf):
    pass


def get_closest_enemy_ice_troll(game, map_object):
    """


    this function return the closest enemy icetroll to the given map object

    :param map_object the map object
    """
    return closest(game, map_object, game.get_enemy_ice_trolls())


'''
def smart_attack_object(game, elf, map_object):
    """

    This function attack with an elf a map object smartly (will run away if gonna take damage)
    if the map object is too far the elf will move towards the map object
    WILL CRASH IF GET NONE

    :param elf: the elf to attck with
    :param map_object: the map_object to attack
    """
    will_be_attacked = False
    if not elf or not map_object:
        print "attack() got None"

    if elf.in_attack_range(map_object):
        if game.get_enemy_living_elves():
            if not get_closest_enemy_elf(game, elf).distance(elf) + game.elf_max_speed > game.elf_attack_range:
                will_be_attacked == True
        for enemy_icetroll in game.get_enemy_ice_trolls():
            if get_closest_my_creature(game, enemy_icetroll).id == elf.id and enemy_icetroll.distance(elf) + game.ice_troll_max_speed > game.ice_troll_attack_range:
                will_be_attacked = True
                break
        if not will_be_attacked:
            elf.attack(map_object)
        elif :
            smart_movement(game, elf, map_object)
    else:
        smart_movement(game, elf, map_object)
'''





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
        if summon_dic[creature_type_str][0]() and game.get_myself().mana_per_turn != 0: # if portal.can_summon_creature
            summon_dic[creature_type_str][1]() # portal.summon_creature
            return True
        else:
            return False


def handle_portals(game):
    ports = game.get_my_portals()
    if len(ports) == 0:
        return
    port_def = closest(game, game.get_my_castle(), ports)
    ports.remove(port_def)
    port_atk = None
    if len(ports) != 0:
        port_atk = ports[0]

    if port_def.distance(game.get_my_castle()) > 2000:
        port_atk = port_def
        port_def = None
    if port_def != None:
        if in_object_range(game, game.get_my_castle(), game.get_enemy_creatures() + game.get_enemy_living_elves(), 3000):
            # print("in if in handle_portals")
            if (game.get_my_ice_trolls() is None or len(game.get_my_ice_trolls()) < 3) or game.get_my_mana() > 200:
                summon(game, port_def, ICE)
    if port_atk != None:
        summon(game, port_atk, LAVA)


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


def turns_to_travel(game, map_object, destination, max_speed=False, smart=False):
    """

    This function calculate the amount of turns a given path will take with an object with a given speed

    :param game:
    :type game: Game
    :param map_object: the start point of the travel
    :param destination: the destination of the travel
    :param max_speed: the speed of the object traveling
    :param smart: if the travel is smart movement
    :type smart: Boolean
    :return: the amount of turns needed to complete the travel
    :type: int
    """

    if not max_speed:
        max_speed = map_object.max_speed

    distance_to_destination = map_object.distance(destination)
    number_of_turns = math.ceil(distance_to_destination/max_speed)

    if smart:
        number_of_dangerous_enemy_unit = 0

        for dangerous_enemy_unit in game.get_enemy_ice_trolls() + game.get_enemy_living_elves():
            sum_distances = dangerous_enemy_unit.distance(map_object) + \
                            dangerous_enemy_unit.distance(destination)
            if math.abs(sum_distances - distance_to_destination) < distance_to_destination * 0.25:
                number_of_dangerous_enemy_unit += 1

        number_of_turns += 3 * number_of_dangerous_enemy_unit

    return number_of_turns


def smart_movement(game, elf, destination):
    """

    This function is moving an given elf towards a given destination safely
    The function will go the the next position which will get the lest damage to the elf
    \n the function wont fear from an enemy unit if that unit is the destination

    :param game:
    :param elf: the elf that need to be moved
    :param destination: the destination to move toward
    :type destination: MapObject
    :return:
    """

    next_turn_my_lava_giant_list, next_turn_enemy_lava_giant_list, next_turn_my_icetrolls_list, \
        next_turn_enemy_icetrolls_list = predict_next_turn_creatures(game)

    possible_movement_points = get_possible_movement_points(game, elf, destination, next_turn_enemy_icetrolls_list)

    my_other_elves = game.get_my_living_elves()
    my_other_elves.remove(elf)  # all my elves beside the given one

    next_turn_my_creatures = next_turn_my_lava_giant_list + next_turn_my_icetrolls_list
    next_turn_enemy_elves_list = predict_next_turn_enemy_elves(game)

    for point in possible_movement_points:  # point is (loc, risk)
        curr_next_turn_elf = copy.deepcopy(elf)
        curr_next_turn_elf.location = point[0]  # the location of point

        for enemy_elf in game.get_enemy_living_elves():
            if enemy_elf == destination:  # if the given elf am trying to get to this elf
                continue  # don't avoid it

            # get curr_next_turn_enemy_elf from next_turn_enemy_elves_list
            for next_turn_elf in next_turn_enemy_elves_list:
                if next_turn_elf.id == enemy_elf.id:
                    curr_next_turn_enemy_elf = next_turn_elf
                    break

            if enemy_elf.in_attack_range(elf):  # if enemy elf in range to attack me
                # then the if the enemy elf attack me he wont move and if he didn't then probably he doesnt want to
                if enemy_elf.distance(point[0]) <= game.elf_attack_range + 10:
                    point[1] += RISK_AMOUNT * game.elf_attack_multiplier * 2
            # else we need to inclde the expected enemy elf next turn location, curr_next_turn_enemy_elf
            elif curr_next_turn_enemy_elf.distance(point[0]) <= game.elf_attack_range + 10:
                point[1] += RISK_AMOUNT * game.elf_attack_multiplier * 2

        for next_turn_enemy_ice_troll in next_turn_enemy_icetrolls_list:
            if next_turn_enemy_ice_troll == destination:
                continue
            # if point location will be the closest to next_turn_enemy_ice_troll from our units
            if closest(game, next_turn_enemy_ice_troll,
                       next_turn_my_creatures + my_other_elves + [curr_next_turn_elf]) == curr_next_turn_elf:
                # then the ice troll will target us so add risk
                point[1] += RISK_AMOUNT
                # if he will also hit us
                if next_turn_enemy_ice_troll.distance(curr_next_turn_elf.location) <= game.ice_troll_attack_range + 10:
                    point[1] += RISK_AMOUNT * game.ice_troll_attack_multiplier * 2

    possible_movement_points.sort(key=lambda possible_point:
                                  possible_point[0].distance(destination) + 1000000 * possible_point[1])

    print "possible_movment_points: %s destination: %s" % (possible_movement_points, destination)
    elf_movement(game, elf, possible_movement_points[0][0])


def get_possible_movement_points(game, elf, destination, next_turn_enemy_icetrolls_list = []):
    """

    This function gets all possible location to move to with an elf
    All the postion will be max_speed distance from the current elf's position
    If the elf can get to the destination, then the destination will be included
    A movement point is the location followed by the risk of the location

    :param game:
    :param elf: the elf which to find all possible movement points
    :param destination: the elf's destination
    :param next_turn_enemy_icetrolls_list: a list of next turn enemy's ice trolls
    :return: a list of all possible *points*
    :type: [[Location, int]]
   """

    circle_points = get_circle(game, elf.get_location(), elf.max_speed)
    possible_movement_points = [[point, 1] for point in circle_points if is_in_game_map(game, point)]

    possible_movement_points.append([elf.get_location(), 1])

    if elf.distance(destination) <= elf.max_speed:
        possible_movement_points.append([destination.get_location(), 1])

    if next_turn_enemy_icetrolls_list:
        optional_danger = next_turn_enemy_icetrolls_list + game.get_enemy_living_elves()
        if optional_danger:
            closest_danger = min(optional_danger, key=lambda danger: danger.distance(elf))
            run_location = elf.get_location().towards(closest_danger, -elf.max_speed)
            if is_in_game_map(game, run_location):
                possible_movement_points.append([run_location, 1])

    print "possible_movement_points:", possible_movement_points
    return possible_movement_points


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
    for angle in xrange(0, 360, 30):
        angle_in_radius = math.radians(angle)
        x_part = int((radius * math.cos(angle_in_radius)))
        y_part = int((radius * math.sin(angle_in_radius)))
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

    if location.row >= game.rows or location.row <= 0:
        return False
    if location.col >= game.cols or location.col <= 0:
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

    next_turn_my_lava_giant_list, next_turn_enemy_lava_giant_list = predict_next_turn_lava_giants(game)
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
        if my_icetroll.current_health == my_icetroll.suffocation_per_turn: # if the troll is going to die
            continue
        next_turn_my_icetroll = copy.deepcopy(my_icetroll)
        next_turn_my_icetroll.current_health -= game.ice_troll_suffocation_per_turn
        target = get_closest_enemy_unit(game, my_icetroll)
        if target and not can_attack(game, my_icetroll, target):
            next_turn_my_icetroll.location = my_icetroll.get_location().towards(target, game.ice_troll_max_speed)
        next_turn_my_icetroll_list.append(next_turn_my_icetroll)

    next_turn_enemy_icetroll_list = []

    for enemy_icetroll in game.get_enemy_ice_trolls():
        if enemy_icetroll.current_health == enemy_icetroll.suffocation_per_turn: # if the troll is going to die
            continue
        next_turn_enemy_icetroll = copy.deepcopy(enemy_icetroll)
        next_turn_enemy_icetroll.current_health -= game.ice_troll_suffocation_per_turn
        target = get_closest_my_unit(game, enemy_icetroll)
        if target and not can_attack(game, enemy_icetroll, target):
            next_turn_enemy_icetroll.location = enemy_icetroll.get_location().towards(target, game.ice_troll_max_speed)
        next_turn_enemy_icetroll_list.append(next_turn_enemy_icetroll)

    # adding new ice trolls
    # print "in predict_next_turn_ice_trolls" + ",".join(str((portal, portal.turns_to_summon)) for portal in game.get_enemy_portals())
    for portal in game.get_all_portals():
        if portal.currently_summoning == "IceTroll" and portal.turns_to_summon == 1:
            new_icetroll = IceTroll()
            new_icetroll.max_speed = game.ice_troll_max_speed
            new_icetroll.attack_range = game.ice_troll_attack_range
            new_icetroll.attack_multiplier = game.ice_troll_attack_multiplier
            new_icetroll.summoner = portal
            new_icetroll.location = portal.get_location()
            new_icetroll.owner = portal.owner
            new_icetroll.type = "IceTroll"
            new_icetroll.id = -1
            new_icetroll.unique_id = -1
            new_icetroll.current_health = game.ice_troll_max_health

            if new_icetroll.owner == game.get_myself():
                next_turn_my_icetroll_list.append(new_icetroll)
            elif new_icetroll.owner == game.get_enemy():
                next_turn_enemy_icetroll_list.append(new_icetroll)
            # print "new IceTroll", new_icetroll, next_turn_enemy_icetroll_list
    return next_turn_my_icetroll_list, next_turn_enemy_icetroll_list


def predict_next_turn_lava_giants(game):
    """

    This function predict the locations of the lava giants for next turn

    :param game:
    :return: the list of my next turn lava giants, the list of the enemy's next turn lava giants
    :type: ([LavaGiants], [LavaGiants])
    """

    next_turn_my_lava_giant_list = []
    target = game.get_enemy_castle()

    for my_lava_giant in game.get_my_lava_giants():
        if my_lava_giant.current_health == my_lava_giant.suffocation_per_turn: # if the giant is going to die
            continue
        next_turn_my_lava_giant = copy.deepcopy(my_lava_giant)
        next_turn_my_lava_giant.current_health -= game.lava_giant_suffocation_per_turn
        if not can_attack(game, my_lava_giant, target):
            next_turn_my_lava_giant.location = my_lava_giant.get_location().towards(target, game.lava_giant_max_speed)
        next_turn_my_lava_giant_list.append(next_turn_my_lava_giant)

    next_turn_enemy_lava_giant_list = []
    target = game.get_my_castle()

    for enemy_lava_giant in game.get_enemy_lava_giants():
        if enemy_lava_giant.current_health == enemy_lava_giant.suffocation_per_turn: # if the giant is going to die
            continue
        next_turn_enemy_lava_giant = copy.deepcopy(enemy_lava_giant)
        next_turn_enemy_lava_giant.current_health -= game.lava_giant_suffocation_per_turn
        if not can_attack(game, enemy_lava_giant, target):
            next_turn_enemy_lava_giant.location = enemy_lava_giant.get_location().towards(target, game.lava_giant_max_speed)
        next_turn_enemy_lava_giant_list.append(next_turn_enemy_lava_giant)

    # adding new lava_giants

    for portal in game.get_all_portals():
        if portal.currently_summoning == "LavaGiant" and portal.turns_to_summon == 1:
            new_lava_giant = LavaGiant()
            new_lava_giant.max_speed = game.lava_giant_max_speed
            new_lava_giant.attack_range = game.lava_giant_attack_range
            new_lava_giant.attack_multiplier = game.lava_giant_attack_multiplier
            new_lava_giant.summoner = portal
            new_lava_giant.location = portal.get_location()
            new_lava_giant.owner = portal.owner
            new_lava_giant.type = "LavaGiant"
            new_lava_giant.id = -1
            new_lava_giant.unique_id = -1
            new_lava_giant.current_health = game.lava_giant_max_health

            if new_lava_giant.owner == game.get_myself():
                next_turn_my_lava_giant_list.append(new_lava_giant)
            elif new_lava_giant.owner == game.get_enemy():
                next_turn_enemy_lava_giant_list.append(new_lava_giant)

    return next_turn_my_lava_giant_list, next_turn_enemy_lava_giant_list


def predict_next_turn_enemy_lava_giants(game):
    """

    This function predict the locations of the lava giants for next turn

    :param game:
    :return: the list of the enemy's next turn lava giants
    :type: [LavaGiants]
    """
    next_turn_enemy_lava_giant_list = []
    target = game.get_my_castle()
    for enemy_lava_giant in game.get_enemy_lava_giants():
        if enemy_lava_giant.current_health == enemy_lava_giant.suffocation_per_turn:  # if the giant is going to die
            continue
        next_turn_enemy_lava_giant = copy.deepcopy(enemy_lava_giant)
        next_turn_enemy_lava_giant.current_health -= game.lava_giant_suffocation_per_turn
        if not can_attack(game, enemy_lava_giant, target):
            next_turn_enemy_lava_giant.location = enemy_lava_giant.get_location().towards(target,
                                                                                          game.lava_giant_max_speed)
        next_turn_enemy_lava_giant_list.append(next_turn_enemy_lava_giant)

        # adding new lava_giants

    for portal in game.get_enemy_portals():
        if portal.currently_summoning == "LavaGiant" and portal.turns_to_summon == 1:
            new_lava_giant = LavaGiant()
            new_lava_giant.max_speed = game.lava_giant_max_speed
            new_lava_giant.attack_range = game.lava_giant_attack_range
            new_lava_giant.attack_multiplier = game.lava_giant_attack_multiplier
            new_lava_giant.summoner = portal
            new_lava_giant.location = portal.get_location()
            new_lava_giant.owner = portal.owner
            new_lava_giant.type = "LavaGiant"
            new_lava_giant.id = -1
            new_lava_giant.unique_id = -1
            new_lava_giant.current_health = game.lava_giant_max_health

            next_turn_enemy_lava_giant_list.append(new_lava_giant)

    return next_turn_enemy_lava_giant_list


def predict_next_turn_given_lava_giants(game, lava_giant_list):
    """

    This function predict the locations of the lava giants for next turn

    :param game:
    :param lava_giant_list: a list of lava giant that the function will return their next turn list
    :return: the list of the given next turn lava giants
    :type: [LavaGiants]
    """
    next_turn_enemy_lava_giant_list = []
    target = game.get_my_castle()
    for enemy_lava_giant in lava_giant_list:
        if enemy_lava_giant.current_health == enemy_lava_giant.suffocation_per_turn:  # if the giant is going to die
            continue
        next_turn_enemy_lava_giant = copy.deepcopy(enemy_lava_giant)
        next_turn_enemy_lava_giant.current_health -= game.lava_giant_suffocation_per_turn
        if not can_attack(game, enemy_lava_giant, target):
            next_turn_enemy_lava_giant.location = enemy_lava_giant.get_location().towards(target,
                                                                                          game.lava_giant_max_speed)
        next_turn_enemy_lava_giant_list.append(next_turn_enemy_lava_giant)

        # adding new lava_giants
        for portal in game.get_enemy_portals():
            if portal.currently_summoning == "LavaGiant" and portal.turns_to_summon == 1:
                new_lava_giant = LavaGiant()
                new_lava_giant.max_speed = game.lava_giant_max_speed
                new_lava_giant.attack_range = game.lava_giant_attack_range
                new_lava_giant.attack_multiplier = game.lava_giant_attack_multiplier
                new_lava_giant.summoner = portal
                new_lava_giant.location = portal.get_location()
                new_lava_giant.owner = portal.owner
                new_lava_giant.type = "LavaGiant"
                new_lava_giant.id = -1
                new_lava_giant.unique_id = -1
                new_lava_giant.current_health = game.lava_giant_max_health

                next_turn_enemy_lava_giant_list.append(new_lava_giant)

    return next_turn_enemy_lava_giant_list


def predict_next_turn_enemy_elves(game):
    """

    This function predict the locations of the enemy's elves for next turn

    :param game:
    :return: a list of next turn enemy's elves with the guessed locations
    :type: [Elf]
    """

    prev_game = Globals.prev_game
    next_turn_enemy_elves_list = []

    for elf in game.get_enemy_living_elves():
        next_turn_elf = copy.deepcopy(elf)
        curr_loc = elf.get_location()
        for prev_elf in prev_game.get_enemy_living_elves():
            if prev_elf.id == elf.id:
                prev_loc = prev_elf.get_location()
                break
        else:
            prev_loc = curr_loc

        nexr_turn_loc = curr_loc.towards(prev_loc, -elf.max_speed)
        next_turn_elf.location = nexr_turn_loc

        next_turn_enemy_elves_list.append(next_turn_elf)

    # print "next_turn_enemy_elves_list: %s" % next_turn_enemy_elves_list
    # print "actual enemy's elves: %s" % game.get_enemy_living_elves()
    return next_turn_enemy_elves_list


def attack_closest_enemy_building(game, elf, max_distance=float("inf")):
    """


    This function attack with an elf the closest building to it

    :param elf:
    :param max_distance: the max distance that the closest building can be
    :return: if an action has been made with the elf
    """

    target = get_closest_enemy_building(gamme, elf)
    if not target:
        return False

    if target.distance(elf) < max_distance:
        attack_object(game, elf, target)
        return True
    else:
        return False


def predict_next_turn_enemy_elves_towards(game, given_enemy_elves, game_object):
    """

    This function predict the locations of the given enemy's elves for next turn

    :param game:
    :param given_enemy_elves
    :param game_object
    :return: a list of next turn enemy's elves with the guessed locations
    :type: [Elf]
    """

    prev_game = Globals.prev_game
    next_turn_enemy_elves_list = []

    for elf in given_enemy_elves:
        next_turn_elf = copy.deepcopy(elf)
        curr_loc = elf.get_location()
        for prev_elf in prev_game.get_enemy_living_elves():
            if prev_elf.id == elf.id:
                prev_loc = prev_elf.get_location()
                break
        else:
            prev_loc = curr_loc

        nexr_turn_loc = curr_loc.towards(game_object, -elf.max_speed)
        next_turn_elf.location = nexr_turn_loc

        next_turn_enemy_elves_list.append(next_turn_elf)

    # print "next_turn_enemy_elves_list: %s" % next_turn_enemy_elves_list
    # print "actual enemy's elves: %s" % game.get_enemy_living_elves()
    return next_turn_enemy_elves_list


def closest_enemy_unit(game, elf, max_distance=float("inf")):
    """

    This function attack with an elf the closest unit to it

    :param elf:
    :param max_distance: the max distance that the closest unit can be
    :return: if an action has been made with the elf
    """

    target = get_closest_enemy_unit(game, elf)
    if not target:
        return False

    if target.distance(elf) < max_distance:
        attack_object(game, elf, target)
        return True
    else:
        return False


def attack_closest_enemy_portal(game, elf, max_distance=float("inf")):
    """

    This function attack with an elf the closest portal to it

    :param elf:
    :param max_distance: the max distance that the closest portal can be
    :return: if an action has been made with the elf
    """

    target = get_closest_enemy_portal(game, elf)
    if not target:
        return False

    if target.distance(elf) < max_distance:
        attack_object(game, elf, target)
        return True
    else:
        return False


def get_closest_enemy_mana_fountain(game, map_object):
    """

    This function return the closest enemy mana fountain to a given map object

    :param map_object: an object on the map in order to find the closest mana fountain to it
    :type map_object: MapObject
    :return: the closest enemy's fountain to map_object
    :type: ManaFountain
    """

    return closest(game, map_object, game.get_enemy_mana_fountains())


def get_closest_enemy_building(game, map_object):
    """

    This function return the closest enemy building to a given map object

    :param map_object: an object on the map in order to find the closest building to it
    :return: the closest enemy's building to map_object
    :type: Building
    """

    enemy_buildings = game.get_enemy_portals() + game.get_enemy_mana_fountains()
    return closest(game, map_object, enemy_buildings)


def build(game, elf, building_type_str, loc=False):
    """

    This function makes a building with a given elf at a specific location \n If the elf isn’t at this position the
    elf will move towards the location safely

    :param game:
    :param elf:
    :param building_type_str:
    :param loc:
    :return:
    """

    build_dic = {
        "portal": (elf.can_build_portal, elf.build_portal),
        "mana fountain": (elf.can_build_mana_fountain, elf.build_mana_fountain)
    }
    if building_type_str not in build_dic.keys():
        return False
    if not elf:
        return False

    if not loc:
        loc = elf.get_location()

    if elf.get_location() == loc:
        if building_type_str == MANA_FOUNTAIN or game.get_myself().mana_per_turn != 0:
            if build_dic[building_type_str][0]():  # if elf.can_build_building()
                build_dic[building_type_str][1]()  # then elf.build_building
                return True
        print ("Elf %s can't build %s at %s" % (elf, building_type_str, loc))
        return False
    else:
        smart_movement(game, elf, loc)
        return True


def attack_closest_enemy_elf(game, elf, max_distance=float("inf")):
    """

    This function attack with an elf the closest elf to it

    :param elf:
    :param max_distance: the max distance that the closest elf can be
    :return: if an action has been made with the elf
    """

    target = get_closest_enemy_elf(game, elf)
    if not target:
        return False

    if target.distance(elf) < max_distance:
        attack_object(game, elf, target)
        return True
    else:
        return False


def attack_closest_enemy_creature(game, elf, max_distance=float("inf")):
    """

    This function attack with an elf the closest creature to it

    :param elf:
    :param max_distance: the max distance that the closest creature can be
    :return: if an action has been made with the elf
    """

    target = get_closest_enemy_creature(game, elf)
    if not target:
        return False

    if target.distance(elf) < max_distance:
        attack_object(game, elf, target)
        return True
    else:
        return False


def check_why_cant_build_building(game, elf, building_radius):
    """

    This function check why an elf cant build a portal in his position.
    The options are amount of mane and buildings in building site

    :param game:
    :param elf:
    :return: if we have enough mana and all pbuildings in building site
    :type: (Bollean, [Portal/ManaFountain]
    """

    buildings_in_range = []
    has_mana = False

    for building in get_disturbing_buildings(game, elf.get_location(), building_radius):
        if building.in_range(elf, 2 * game.portal_size):
            buildings_in_range.append(building)

    if game.get_my_mana() >= game.portal_cost:
        has_mana = True
    else:
        has_mana = False

    why_cant_build_portal = namedtuple("why_cant_build_portal", ["has_mana", "portals_in_range"])
    return why_cant_build_portal(has_mana, buildings_in_range)


def get_dangerous_enemy_lava_giant(game):
    """

    This function get all dangerous enemy lava giant which mean they are close enough to do significant to my castle
    The function will include the damage that the lava_giant will get this turn

    :param game:
    :return: a list of all the dangerous enemy's lava giants
    :type: [LavaGiant]
    """

    close_enough_enemy_lava_giant = []

    for lava_giant in game.get_enemy_lava_giants():
        turns_to_castle = turns_to_travel(game, lava_giant,
                                          game.get_my_castle().get_location().towards(lava_giant,
                                                                                      game.lava_giant_attack_range +
                                                                                      game.castle_size))

        max_turns_to_castle = 6
        if turns_to_castle > max_turns_to_castle:  # if the lava giant is far, ice troll will berle affect him
            continue
        curr_health = lava_giant.current_health
        for my_ice_troll in is_targeted_by_my_icetroll(game, lava_giant):
            if can_attack(game, my_ice_troll, lava_giant):
                curr_health -= game.ice_troll_attack_multiplier

        hp_left = curr_health - (turns_to_castle * lava_giant.suffocation_per_turn)
        if hp_left > 2:
            close_enough_enemy_lava_giant.append(lava_giant)

    return close_enough_enemy_lava_giant


def is_enemy_elf_attacking_elves(game):
    """

    This function check if enemy's elves have to ability of attacking out elves
    If the enemy elves had attack our even once the function will return True

    :param game:
    :return: if enemy elves have the ability of attacking our elves
    """

    last_turn_game = Globals.prev_game

    if Globals.is_enemy_elf_attacking:
        return True
    else:
        for last_turn_my_elf in last_turn_game.get_my_living_elves():
            curr_turn_my_elf = get_by_unique_id(game, last_turn_my_elf.unique_id)
            if not curr_turn_my_elf:
                continue
            # get curr turn hp if only ice trolls have attacked last_turn_my_elf
            curr_turn_expected_hp = get_my_unit_next_turn_health(last_turn_game, last_turn_my_elf,
                                                                 include_elves=False)

            if curr_turn_my_elf.current_health < curr_turn_expected_hp:  # if the actual hp is lower
                for curr_turn_enemy_elf in game.get_enemy_living_elves():
                    if not has_moved(game, curr_turn_enemy_elf):  # if the enemy elf hasn't move
                        if not curr_turn_enemy_elf.is_building:  # and he doesn't build a portal
                            if curr_turn_enemy_elf.in_attack_range(last_turn_my_elf):  # and he is in range to hit me
                                Globals.is_enemy_elf_attacking = True  # then the enemy elf have attacked my elf
                                return True
    return False


def get_my_unit_next_turn_health(game, my_unit, include_elves=False):
    """

    This function predict a given enemy unit next turn health
    The function can include possible enemy elves attack depend on the *include_elves* parameter

    :param game:
    :param my_unit: the enemy unit to predict it's next turn hp
    :param include_elves: a flag to represent if to include enemy elves possible attacks
    :type include_elves: Boolean
    :return: the predicted next turn *my_unit* hp
    """

    start_time = time.time()
    print "get_my_unit_next_turn_health"
    next_turn_hp = my_unit.current_health
    ice_trolls_that_target_me = is_targeted_by_enemy_icetroll(game, my_unit)
    print "get_my_unit_next_turn_healthtime: %s", (time.time()*1000-start_time*1000)
    if isinstance(my_unit, Creature):
        next_turn_hp -= my_unit.suffocation_per_turn

    for close_ice_troll in ice_trolls_that_target_me:
            if can_attack(game, close_ice_troll, my_unit):
                next_turn_hp -= game.ice_troll_attack_multiplier

    if include_elves and is_enemy_elf_attacking_elves(game):
        for enemy_elf in game.get_enemy_living_elves():
            if enemy_elf.in_attack_range(my_unit):
                next_turn_hp -= game.elf_attack_multiplier

    return next_turn_hp


def can_attack(game, attacking_unit, target):
    """

    This function check if an given unit can attack another given unit

    :param game:
    :param attacking_unit: the unit to check if can attack
    :param target: the map object to check if can get hit
    :type target: MapObject
    :return: if attacking_unit in range to attack defending_unit
    """

    return attacking_unit.in_range(target, attacking_unit.attack_range)


def get_by_unique_id(game, need_to_find_unique_id):
    """

    This function gets a game object by a given unique id from game

    :param game:
    :param need_to_find_unique_id:
    :type need_to_find_unique_id: Int
    :return: The game object from game with the given unique id
    :type: GameObject
    """

    my_game_objects = get_player_units(game, game.get_myself()) + game.get_my_portals()
    enemy_game_objects = get_player_units(game, game.get_enemy()) + game.get_enemy_portals()
    all_game_objects = my_game_objects + enemy_game_objects

    for game_object in all_game_objects:
        if game_object.unique_id == need_to_find_unique_id:
            return game_object

    return None


def get_farthest_enemy_portal(game, map_object):
    """

    This function return the farthest enemy portal to a given map object

    :param map_object: an object on the map in order to find the farthest portal to it
    :return: the closest enemy's portal to map_object
    :type: Portal
    """

    return farthest(game, map_object, game.get_enemy_portals())


def get_enemy_buildings(game):
    """

    This function return the enemy's buildings list
    :return: a list of the enemy's buildings
    :type: [building]
    """
    enemy_buildings = game.get_all_buildings()
    for building in enemy_buildings:
        if building.owner == game.get_myself():
            enemy_buildings.remove(building)
    return enemy_buildings


def get_closest_enemy_building(game, map_object):
    """

    This function return the farthest enemy portal to a given map object

    :param map_object: an object on the map in order to find the farthest portal to it
    :return: the closest enemy's portal to map_object
    :type: Portal
    """

    return closest(game, map_object, game.get_enemy_buildings())


def get_player_units(game, need_to_find_player):
    """

    This function gets all units of a giving player

    :param game:
    :param need_to_find_player: the player which units to return
    :return: a list of all units which belong to the given player
    :type: [Creature/Elf]
    """

    for player in game.get_all_players():
        if player == need_to_find_player:
            return player.living_elves + player.creatures


def has_moved(game, unit_to_check):
    """

    This function check if a given unit has moved in the last turn

    :param game:
    :param unit_to_check:
    :type unit_to_check: Elf/Creature
    :return: if the given unit had moved in the last turn
    :type: Boolean
    """

    last_turn_game = Globals.prev_game
    last_turn_my_units = get_player_units(last_turn_game, game.get_myself())
    last_turn_enemy_units = get_player_units(last_turn_game, game.get_enemy())
    last_turn_all_units = last_turn_enemy_units + last_turn_my_units

    for last_turn_unit in last_turn_all_units:
        if last_turn_unit.unique_id == unit_to_check.unique_id:
            if last_turn_unit.get_location() != unit_to_check.get_location():
                return True
            else:
                return False

    return True  # the unit has just spawn


def get_objects_in_path(game, first_path_edge, second_path_edge, possible_map_objects_in_path, offset=100):
    """

    This function look for map objects that are on the path from one point to another from a given list of map objects

    :param game:
    :param first_path_edge: the first edge of the path
    :param second_path_edge: the second edge of the path
    :param possible_map_objects_in_path: the list of map object to search in
    :type possible_map_objects_in_path: [MapObject]
    :param offset: the amount of flexibility for a map object to be count as on he way
    :return: the list of all map object that are on the path from *possible_map_objects_in_path*
    """

    total_distance = first_path_edge.distance(second_path_edge)
    map_objects_in_way = []

    for map_object in possible_map_objects_in_path:
        distance_to_first_edge = map_object.distance(first_path_edge)
        distance_to_second_edge = map_object.distance(second_path_edge)

        if distance_to_first_edge + distance_to_second_edge < total_distance + offset:
            map_objects_in_way.append(map_object)

    return map_objects_in_way


def get_closest_my_building(game, game_object):
    """

    This function return the closest building of me to the given game object


    :param game:
    :param game_object: in order to check what is the closest building to it
    :return: Building
    """
    return closest(game, game_object, get_my_buildings(game))


def swap_players(func):  # this is a decorators for doubling a function with swaped players
    def swaped_func(game, *args):
        swaped_game = copy.deepcopy(game)
        swaped_game._hx___me, swaped_game._hx___enemies = game.get_enemy(), [game.get_myself()]
        return func(swaped_game, *args)
    return swaped_func


get_my_buildings = swap_players(get_enemy_buildings)
get_my_buildings.__doc__ = \
    """

    This function return the my buildings list
    :return: a list of the enemy's buildings
    :type: [building]
    """


get_closest_my_portal = swap_players(get_closest_enemy_portal)
get_closest_my_portal.__doc__ = \
    """

    This function return the closest portal of my portals to a given map object

    :param map_object: an object on the map in order to find the closest portal to it
    :return: the closest my portal to map_object
    :type: Portal
    """

get_farthest_my_portal = swap_players(get_farthest_enemy_portal)
get_farthest_my_portal.__doc__ = \
    """

    This function return the farthest portal of my portals to a given map object

    :param map_object: an object on the map in order to find the farthest portal to it
    :return: the farthest my portal to map_object
    :type: Portal
    """

get_closest_my_unit = swap_players(get_closest_enemy_unit)
get_closest_my_unit.__doc__ = \
    """

    This function return the closest unit(creature + elf) of my units to a given map object

    :param map_object: an object on the map in order to find the closest unit to it
    :return: the closest my unit to map_object
    :type: Creature/Elf
    """

get_closest_my_elf = swap_players(get_closest_enemy_elf)
get_closest_my_elf.__doc__ = \
    """

    This function return the closest elf of my elves to a given map object

    :param map_object: an object on the map in order to find the closest elf to it
    :return: the closest my elf to map_object
    :type: Elf
    """

get_closest_my_creature = swap_players(get_closest_enemy_creature)
get_closest_my_creature.__doc__ = \
    """

    This function return the closest creature of my creatures to a given map object

    :param map_object: an object on the map in order to find the closest creature to it
    :return: the closest my creature to map_object
    :type: Creature
    """

is_targeted_by_my_icetroll = swap_players(is_targeted_by_enemy_icetroll)
is_targeted_by_my_icetroll.__doc__ = \
    """

    This function returns a list of all the my ice trolls who target a given map object.
    if the returned list is empty then the given map object is safe

    :param map_object: the map object which to check if is targeted bt ice trolls
    :type map_object: MapObject
    :return: return a list of the ice trolls which target obj
    :type: [IceTroll]
    """

get_enemy_unit_next_turn_health = swap_players(get_my_unit_next_turn_health)
get_enemy_unit_next_turn_health.__doc__ = \
    """

    This function predict a given enemy unit next turn health
    The function can include possible elves attack depend on the *include_elves* parameter

    :param game:
    :param my_unit: the enemy unit to predict it's next turn hp
    :param include_elves: a flag to represent if to include elves possible attacks
    :type include_elves: Boolean
    :return: the predicted next turn *my_unit* hp
    """


get_closest_my_mana_fountain = swap_players(get_closest_enemy_mana_fountain)
get_closest_my_mana_fountain.__doc__ = \
    """

    This function return the closest of my mana fountain to a given map object

    :param map_object: an object on the map in order to find the closest mana fountain to it
    :return: the closest my mana fountain to map_object
    :type: ManaFountain
    """


get_closest_my_building = swap_players(get_closest_enemy_building)
get_closest_my_building.__doc__ = \
    """

    This function return the closest of my building to a given map object

    :param map_object: an object on the map in order to find the closest building to it
    :return: the closest my building to map_object
    :type: Building
    """


def summon_with_closest_portal(game, creature_type_str, target, portal_list=False):
    """

    This function summon a creature with the closest available portal

    :param game:
    :type game: Game
    :param creature_type_str:
    :type creature_type_str: String
    :param target:
    :type target: MapObject
    :param portal_list:
    :type portal_list: [Portal]
    :return:
    """

    print "in summon_with_closest_portal"
    if not portal_list:
        portal_list = game.get_my_portals()

    sorted_portal_list = sorted(portal_list, key=lambda portal: portal.distance(target))

    for portal in sorted_portal_list:
        if summon(game, portal, creature_type_str):
            return True

    return False


def farthest(game, main_map_object, map_objects_list):
    """

    This function get a main map object and a list of map object and return the farthest map object (from the list)
    to the main map object

    :param main_map_object: the map object which to find the farthest to
    :type main_map_object: MapObject
    :param map_objects_list: the list of map objects from which to find the farthest object to main_map_object
    :type map_objects_list: [MapObject]
    :return: a map object from map_objects_list which is the farthest to main_map_object
    :type: MapObject
    """
    if not map_objects_list:
        return None
    else:
        return max(map_objects_list, key=lambda map_object: main_map_object.distance(map_object))


def update_dangerous_enemy_portals(game):

    dangerous_enemy_portals = Globals.possible_dangerous_enemy_portals
    for portal in game.get_enemy_portals():
        if portal.currently_summoning == "LavaGiant" and portal.turns_to_summon == 3:
            portal_queue = dangerous_enemy_portals.get(portal, [])
            portal_queue.append(game.turn)
            if len(portal_queue) > 3:
                portal_queue.remove(portal_queue[0])
            dangerous_enemy_portals[portal] = portal_queue
    for portal in copy.deepcopy(Globals.possible_dangerous_enemy_portals):
        if portal not in game.get_enemy_portals():
            Globals.possible_dangerous_enemy_portals.pop(portal, None)


def get_disturbing_buildings(game, loc, radius=0):
    """

    This function finds all the disturbing buildings to loc

    :param game:
    :param loc:
    :param radius:
    :return: a list of all the disturbing buildings
    """

    disturbing_buildings = []
    for building in [game.get_my_castle(), game.get_enemy_castle()] + game.get_all_portals() + game.get_all_mana_fountains():
        if building.distance(loc) < radius + building.size:
            disturbing_buildings.append(building)

    return disturbing_buildings


def how_much_hp_in_x_turns(game, game_object, turns = 1):
    """

    This function gets a map object calculate the hp he will have in the in the given turns from now
    (in the current state of the game)(the worst case scenario)

    :param game_object: the game object in order to calculate it's hp in the given turns
    :type game_object: GameObject
    :param turns: the number of turns
    :type turns: int
    :return: the hp of the given map object
    :type: int
    """
    i = turns
    health = game_object.current_health
    next_turn_elves = game.get_enemy_living_elves()
    if game_object.__str__() == "Castle":
        while i > 0:
            if game.get_enemy_lava_giants():
                lava_giants_list = game.get_enemy_lava_giants()
                if turns > 1:
                    for enemy_lava_giant in predict_next_turn_given_lava_giants(game, lava_giants_list):
                        if enemy_lava_giant.location.distance() == game.lava_giant_attack_range:
                            health = health - game.lava_giant_attack_multiplier
                else:
                    for enemy_lava_giant in lava_giants_list:
                        if enemy_lava_giant.location.distance() == game.lava_giant_attack_range:
                            health = health - game.lava_giant_attack_multiplier
            i = i - 1
    if game.get_enemy_living_elves():
        enemy_elves_list = game.get_enemy_elves()
        i = turns
        while i > 0:
            if turns > 1:
                for enemy_elf in next_turn_elves:
                    next_turn_elves = predict_next_turn_enemy_elves_towards(game, enemy_elves_list, get_closest_my_building(game, enemy_elf))
                    if enemy_elf.location.distance() == game.elf_attack_range:
                        health = health - game.elf_attack_multiplier
            i = i - 1
    return health


def hunt_enemy_elf_with_wall(game, enemy_elf, use_casts = False):
    """
    This function tries to hunt the given elf with a wall

    :param game:
    :param enemy_elf: the elf to hunt
    :param use_casts if the function can use casts in order to kill the enemy elf
    :return: nothing
    """
    if len(game.get_my_living_elves()) == 2:
        distance_from_col = math.fabs(enemy_elf.location.col - game.cols)
        distance_from_row = math.fabs(enemy_elf.location.row - game.rows)
        if distance_from_col < game.cols / 2:
            closest_col = game.cols
        else:
            closest_col = 0

        if distance_from_row < game.rows / 2:
            closest_row = game.rows
        else:
            closest_row = 0

        elf1 = game.get_my_living_elves()[0]
        elf2 = game.get_my_living_elves()[1]

        if Location(closest_row, enemy_elf.location.col).distance(enemy_elf) < Location(enemy_elf.location.row,
                                                                                        closest_col).distance(
                enemy_elf):
            closest_wall = closest_row
            if game.get_my_living_elves()[0].distance(Location(closest_wall,
                                                               game.get_my_living_elves()[0].location.col)) < \
                    game.get_my_living_elves()[1].distance(
                        Location(closest_wall, game.get_my_living_elves()[1].location.col)):
                chasing_elf = elf1
                reacting_elf = elf2
                print "chasing_elf: ", chasing_elf
                print "reacting elf: ", reacting_elf
            else:
                chasing_elf = elf2
                reacting_elf = elf1
                print "chasing_elf: ", chasing_elf
                print "reacting elf: ", reacting_elf
        else:
            closest_wall = closest_col
        if game.get_my_living_elves()[0].distance(
                Location(game.get_my_living_elves()[0].location.row, closest_wall)) < game.get_my_living_elves()[
            1].distance(Location(game.get_my_living_elves()[1].location.row, closest_wall)):
            chasing_elf = elf1
            print "chasing_elf: ", chasing_elf
            print "reacting elf: ", reacting_elf
        else:
            chasing_elf = elf2
            reacting_elf = elf1
            print "chasing_elf: ", chasing_elf
            print "reacting elf: ", reacting_elf
        print "closest col ", closest_col
        print "closest_row ", closest_row

        chasing_elf_distance = chasing_elf.distance(enemy_elf)
        blocking_elf_distance = reacting_elf.distance(enemy_elf)
        current_distance_between_elves = reacting_elf.distance(chasing_elf)

        if chasing_elf_distance <= blocking_elf_distance + turns_to_travel(game, elf2, elf1,
                                                                           game.elf_max_speed) * game.speed_up_expiration_turns and use_casts:
            if game.get_my_mana > game.speed_up_cost and not is_have_speed_up(game, chasing_elf):
                reacting_elf.cast_speed_up()

        elif blocking_elf_distance <= chasing_elf_distance + turns_to_travel(game, elf1, elf2,
                                                                             game.elf_max_speed) * game.speed_up_expiration_turns and use_casts:
            if game.get_my_mana > game.speed_up_cost and not is_have_speed_up(game, chasing_elf):
                chasing_elf.cast_speed_up()

        prev_enemy_elf_location = get_by_unique_id(Globals.prev_game, enemy_elf.unique_id).location
        location_differnce = enemy_elf.location.subtract(prev_enemy_elf_location)
        best_loc = chasing_elf.location

        if closest_wall == closest_col:
            if chasing_elf_distance <= game.elf_attack_range and math.fabs(
                    Location(enemy_elf.row, closest_col).distance(chasing_elf) - enemy_elf.location.towards(
                            chasing_elf_distance)) < 150:
                if not chasing_elf.already_acted:
                    print "entered if"
                    attack_object(game, chasing_elf, enemy_elf)

            elif chasing_elf_distance <= game.elf_attack_range and math.fabs(
                    Location(closest_row, enemy_elf.col).distance(chasing_elf) - enemy_elf.location.towards(
                            chasing_elf_distance)) < 150:
                if not chasing_elf.already_acted:
                    print "entered elif"
                    attack_object(game, chasing_elf, enemy_elf)

            else:
                print "entered else"
                minimal_distance = 9999
                for possible_location in get_possible_movement_points(game, chasing_elf, enemy_elf):
                    if closest_wall == closest_row:
                        if math.fabs(possible_location[0].distance(Location(closest_wall, chasing_elf.location.col)) -
                                     possible_location[0].distance(
                                             enemy_elf.location.towards(chasing_elf, chasing_elf_distance))) < 50:
                            if possible_location[0].distance(chasing_elf.location.towards(enemy_elf.location,
                                                                                          chasing_elf.distance(
                                                                                                  enemy_elf) - game.elf_max_speed)) < minimal_distance:
                                best_loc = possible_location[0]
                                minimal_change = chasing_elf.distance(reacting_elf) + chasing_elf.distance(closest_wall,
                                                                                                           chasing_elf.col)

                    elif math.fabs(possible_location[0].distance(Location(chasing_elf.location.row, closest_wall))):
                        if possible_location[0].distance(chasing_elf.location.towards(enemy_elf.location,
                                                                                      chasing_elf.distance(
                                                                                              enemy_elf) - game.elf_max_speed)) < minimal_distance:
                            best_loc = possible_location[0]
                            minimal_change = chasing_elf.distance(reacting_elf) + chasing_elf.distance(closest_wall,
                                                                                                       chasing_elf.col)

                if best_loc != chasing_elf.location and not chasing_elf.already_acted:
                    chasing_elf.move_to(best_loc)
                elif not chasing_elf.already_acted:
                    chasing_elf.move_to(enemy_elf)

            if blocking_elf_distance < game.elf_attack_range and math.fabs(
                    closest_wall.distance(reacting_elf) - enemy_elf.location.towards(blocking_elf_distance) < 50) and not reacting_elf.already_acted:
                attack_object(game, reacting_elf, enemy_elf)
            elif not reacting_elf.already_acted:
                minimal_distance = 9999
                for possible_location in get_possible_movement_points(game, elf2, enemy_elf):
                    print "minimal_distance: ", minimal_distance
                    print "possible distance: ", possible_location[0].distance(
                        reacting_elf.location.towards(enemy_elf.location, elf1.distance(enemy_elf) - game.elf_max_speed))
                    print "possible_location.distance(elf1): ", possible_location[0].distance(reacting_elf)
                    if math.fabs(possible_location[0].distance(reacting_elf) - current_distance_between_elves) <= 50:
                        if possible_location[0].distance(elf1.location.towards(enemy_elf.location, reacting_elf.distance(
                                enemy_elf) - game.elf_max_speed)) < minimal_distance:
                            best_loc = possible_location[0]
                            minimal_distance = possible_location[0].distance(elf1.location.towards(enemy_elf.location,
                                                                                                   reacting_elf.distance(
                                                                                                       enemy_elf) - game.elf_max_speed))
                print "best loc: ", best_loc
                if best_loc != reacting_elf.location:
                    reacting_elf.move_to(best_loc)
                else:
                    reacting_elf.move_to(enemy_elf)

    else:
        print "we don't have 2 elves alive"
    ## check if enemy elf can get farther if he can don't attack him




'''
def hunt_enemy_elf_with_wall(game, enemy_elf, use_casts=False):
    """
    This function tries to hunt the given elf with a wall

    :param game:
    :param enemy_elf: the elf to hunt
    :param use_casts if the function can use casts in order to kill the enemy elf
    :return: nothing
    """
    if len(game.get_my_living_elves()) == 2:
        distance_from_col = math.fabs(enemy_elf.location.col - game.cols)
        distance_from_row = math.fabs(enemy_elf.location.row - game.rows)
        if distance_from_col < game.cols / 2:
            closest_col = game.cols
        else:
            closest_col = 0

        if distance_from_row < game.rows / 2:
            closest_row = game.rows
        else:
            closest_row = 0

        elf1 = game.get_my_living_elves()[0]
        elf2 = game.get_my_living_elves()[1]
        my_elves = [elf1, elf2]

        if Location(closest_row, enemy_elf.location.col).distance(enemy_elf) < Location(enemy_elf.location.row,
                                                                                        closest_col).distance(
            enemy_elf):
            closest_wall = closest_row
        else:
            closest_wall = closest_col

        elf1_dis = elf1.distance(enemy_elf)
        elf2_dis = elf2.distance(enemy_elf)
        current_distance_between_elves = elf1.distance(elf2)

        if game.elf_max_speed * game.speed_up_multiplier * game.speed_up_expiration_turns <= elf1.distance(
                elf2) and elf1_dis < elf2_dis and use_casts:
            elf1.cast_speed_up()
        elif game.elf_max_speed * game.speed_up_multiplier * game.speed_up_expiration_turns <= elf2.distance(
                elf1) and elf1_dis < elf2_dis and use_casts:
            elf2.cast_speed_up()

        prev_enemy_elf_location = get_by_unique_id(Globals.prev_game, enemy_elf.unique_id).location
        location_differnce = enemy_elf.location.subtract(prev_enemy_elf_location)
        best_loc = elf1.get_location()

        if closest_wall == closest_col:
            for elf in my_elves:
                if elf == elf1:
                    other_elf = elf2
                else:
                    other_elf = elf1

                print "closest_wall = ", closest_wall
                print "distance between elves - distance from enemy elf: ", math.fabs(
                    elf.distance(other_elf) - elf.distance(enemy_elf))

                if elf.distance(other_elf) <= game.elf_attack_range:
                    if math.fabs(elf.distance(other_elf) - elf.distance(enemy_elf)) < 150 or closest(game, enemy_elf,
                                                                                                     my_elves) == elf:
                        aggressive_attack_object(game, elf, enemy_elf)


                else:
                    smallest_difference = 9999
                    best_loc = elf.location
                    circle_points = get_circle(game, elf.get_location(), elf.max_speed)
                    possible_movement_points = [[point, 1] for point in circle_points if is_in_game_map(game, point)]

                    possible_movement_points.append([elf.get_location(), 1])
                    for possible_location in possible_movement_points:
                        if math.fabs(
                                possible_location[0].distance(
                                    Location(enemy_elf.get_location().row, closest_wall).towards(enemy_elf,
                                                                                                 closest(game,
                                                                                                         enemy_elf,
                                                                                                         my_elves).distance(
                                                                                                     enemy_elf))) +
                                possible_location[0].distance(other_elf)) < smallest_difference:
                            best_loc = possible_location[0]
                            smallest_difference = math.fabs(
                                possible_location[0].distance(
                                    Location(enemy_elf.get_location().row, closest_wall).towards(enemy_elf,
                                                                                                 closest(game,
                                                                                                         enemy_elf,
                                                                                                         my_elves).distance(
                                                                                                     enemy_elf))) +
                                possible_location[0].distance(other_elf))
                        else:
                            best_loc = elf.get_location().towards(enemy_elf.get_location(), game.elf_max_speed)
                    if elf.location != best_loc:
                        print "moved to best loc"
                        elf.move_to(best_loc)


        else:
            for elf in my_elves:
                if elf == elf1:
                    other_elf = elf2
                else:
                    other_elf = elf1

                print "closest_wall = ", closest_wall
                print "distance between elves - distance from enemy elf: ", math.fabs(
                    elf.distance(other_elf) - elf.distance(enemy_elf))
                if math.fabs(elf.distance(other_elf) - elf.distance(enemy_elf)) < 150 or closest(game, enemy_elf,
                                                                                                 my_elves) == elf:
                    aggressive_attack_object(game, elf, enemy_elf)

                else:
                    smallest_difference = 9999
                    best_loc = elf.location
                    circle_points = get_circle(game, elf.get_location(), elf.max_speed)
                    possible_movement_points = [[point, 1] for point in circle_points if is_in_game_map(game, point)]

                    possible_movement_points.append([elf.get_location(), 1])
                    for possible_location in possible_movement_points:
                        if math.fabs(
                                possible_location[0].distance(
                                    Location(closest_wall, enemy_elf.get_location().col).towards(enemy_elf,
                                                                                                 closest(game,
                                                                                                         enemy_elf,
                                                                                                         my_elves).distance(
                                                                                                     enemy_elf))) +
                                possible_location[0].distance(other_elf) - possible_location[
                                    0].distance()) < smallest_difference:
                            best_loc = possible_location[0]
                            smallest_difference = math.fabs(
                                possible_location[0].distance(
                                    Location(closest_wall, enemy_elf.get_location().col).towards(enemy_elf,
                                                                                                 closest(game,
                                                                                                         enemy_elf,
                                                                                                         my_elves).distance(
                                                                                                     enemy_elf))) * 4 + 0.75 *
                                possible_location[0].distance(other_elf))
                        else:
                            best_loc = elf.get_location().towards(enemy_elf.get_location(), game.elf_max_speed)
                    if elf.location != best_loc:
                        print "moved to best loc"
                        elf.move_to(best_loc)

    else:
        print "we don't have 2 elves alive"
    ## check if enemy elf can get farther if he can don't attack him
'''