# coding=utf-8
"""
############
trainingBot
############
.. module:: trainingBot
   :platform: Unix, Windows
   :synopsis: A useful module indeed.

.. moduleauthor:: Andrew Carter <andrew@invalid.com>
b

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
    return_value = []
    if Globals.who_target_me_dic.get(map_object):
        return_value = Globals.who_target_me_dic[map_object]

    # print "$&^$&^ is_targeted_by_enemy_icetroll map_object: %s, return %s" % (map_object, return_value)
    return return_value


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
        return min(map_objects_list, key=lambda map_object: main_map_object.distance(map_object))


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
        if Globals.portal_activeness[
            port.id] < life_expectancy_of_lava_giant - turns_to_castle:  # the closer a portal is to our castle the more aware we want to be
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
                defense_positions.append(pos.towards(pos2, pos.distance(pos2) / 2))
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


def handle_defensive_elf(game, elf):
    pass


def get_closest_enemy_ice_troll(game, map_object):
    """


    this function return the closest enemy icetroll to the given map object

    :param map_object the map object
    """
    return closest(game, map_object, game.get_enemy_ice_trolls())


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
        if summon_dic[creature_type_str][0]() and game.get_myself().mana_per_turn != 0:  # if portal.can_summon_creature
            summon_dic[creature_type_str][1]()  # portal.summon_creature
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
        if in_object_range(game, game.get_my_castle(), game.get_enemy_creatures() + game.get_enemy_living_elves(),
                           3000):
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
    number_of_turns = math.ceil(distance_to_destination / max_speed)

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
    start_time = time.time()
    # print "start smart_movement time: %s" % (time.time()*1000-start_time*1000)

    if elf.invisible and get_invisiblety_spell(game, elf).expiration_turns > 1:
        elf_movement(game, elf, destination)
        return

    next_turn_my_lava_giant_list, next_turn_enemy_lava_giant_list, next_turn_my_icetrolls_list, \
    next_turn_enemy_icetrolls_list = predict_next_turn_creatures(game)

    get_hit_set = set()
    possible_movement_points = get_possible_movement_points(game, elf, destination, next_turn_enemy_icetrolls_list)

    my_other_elves = game.get_my_living_elves()
    my_other_elves.remove(elf)  # all my elves beside the given one

    next_turn_my_creatures = next_turn_my_lava_giant_list + next_turn_my_icetrolls_list
    next_turn_enemy_elves_list = predict_next_turn_enemy_elves(game)

    # print "im smart_movement after init time: %s" % (time.time()*1000-start_time*1000)
    enemy_icetrolls_target_dis = {}
    for next_turn_enemy_ice_troll in next_turn_enemy_icetrolls_list:
        target = closest(game, next_turn_enemy_ice_troll, next_turn_my_creatures + my_other_elves)
        if target:
            distance_to_target = next_turn_enemy_ice_troll.distance(target)
            enemy_icetrolls_target_dis[next_turn_enemy_ice_troll] = distance_to_target
    # print "im smart_movement after ice trolls targets time: %s" % (time.time()*1000-start_time*1000)

    for point in possible_movement_points:  # point is (loc, risk)
        curr_next_turn_elf = copy.deepcopy(elf)
        curr_next_turn_elf.location = point[0]  # the location of point
        if is_enemy_elf_attacking_elves(game):
            for enemy_elf in game.get_enemy_living_elves():
                if enemy_elf == destination:  # if the given elf am trying to get to this elf
                    continue  # don't avoid it

                # get curr_next_turn_enemy_elf from next_turn_enemy_elves_list
                for next_turn_elf in next_turn_enemy_elves_list:
                    if next_turn_elf.id == enemy_elf.id:
                        curr_next_turn_enemy_elf = next_turn_elf
                        break

                if enemy_elf.in_attack_range(elf):  # if enemy elf in range to attack me
                    # print "h& , elf_attack_range %s elf_max_speed %s" % (game.elf_attack_range, game.elf_max_speed)
                    # then the if the enemy elf attack me he wont move and if he didn't then probably he doesnt want to
                    if enemy_elf.distance(point[0]) <= game.elf_attack_range:  # +10
                        # print "point %s close so enemy elf: %s" % (point[0], enemy_elf)
                        point[1] += RISK_AMOUNT * game.elf_attack_multiplier * 2
                        get_hit_set.add(point[0])
                # else we need to inclde the expected enemy elf next turn location, curr_next_turn_enemy_elf
                elif curr_next_turn_enemy_elf.distance(point[0]) <= game.elf_attack_range:
                    point[1] += RISK_AMOUNT * game.elf_attack_multiplier * 2
                    get_hit_set.add(point[0])

        for next_turn_enemy_ice_troll in next_turn_enemy_icetrolls_list:
            if next_turn_enemy_ice_troll == destination:
                continue
            distance_to_enemy_icetroll = next_turn_enemy_ice_troll.distance(curr_next_turn_elf)
            # print "ice troll %s ,distance_to_enemy_icetroll %s, target point: %s," % (next_turn_enemy_ice_troll, distance_to_enemy_icetroll, point)
            # print "enemy_icetroll_target_dis: %s" % (enemy_icetrolls_target_dis.get(next_turn_enemy_ice_troll, float("inf")))
            # if point location will be the closest to next_turn_enemy_ice_troll from our units
            if distance_to_enemy_icetroll <= enemy_icetrolls_target_dis.get(next_turn_enemy_ice_troll, float("inf")):
                # then the ice troll will target us so add risk
                point[1] += RISK_AMOUNT
                # if he will also hit us
                if distance_to_enemy_icetroll <= game.ice_troll_attack_range:
                    point[1] += RISK_AMOUNT * game.ice_troll_attack_multiplier * 2
                    get_hit_set.add(point[0])
    print "im smart_movement after loop time: %s" % (time.time() * 1000 - start_time * 1000)

    best_point = min(possible_movement_points, key=lambda possible_point:
    possible_point[0].distance(destination) + 1000000 * possible_point[1])
    print "possible_movement_points:", possible_movement_points
    print "best_point: %s destination: %s" % (best_point, destination)
    if best_point[0] in get_hit_set:  # no place is safe
        if elf.can_cast_invisibility():
            elf.cast_invisibility()
            print "invisibility!"
            return
        """
        closest_enemy_unit = get_closest_enemy_unit(game, elf)
        if does_win_fight(game, elf, closest_enemy_unit) and elf.in_attack_range(closest_enemy_unit):
            attack_object(game, elf, get_closest_enemy_unit(game, elf))
            return
        """
    print "im smart_movement end time: %s" % (time.time() * 1000 - start_time * 1000)

    elf_movement(game, elf, best_point[0])


def get_possible_movement_points(game, elf, destination, next_turn_enemy_icetrolls_list):
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

    optional_danger = next_turn_enemy_icetrolls_list + game.get_enemy_living_elves()
    if optional_danger:
        closest_danger = min(optional_danger, key=lambda danger: danger.distance(elf))
        run_location = elf.get_location().towards(closest_danger, -elf.max_speed)
        if is_in_game_map(game, run_location):
            possible_movement_points.append([run_location, 1])

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
    for angle in xrange(0, 360, 10):
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

    return next_turn_my_lava_giant_list, next_turn_enemy_lava_giant_list, \
           next_turn_my_icetrolls_list, next_turn_enemy_icetrolls_list


def predict_next_turn_ice_trolls(game):
    """

    This function predict the locations of the ice trolls for next turn

    :param game:
    :return: the list of my next turn trolls, the list of the enemy's next turn trolls
    :type: ([IceTroll], [IceTroll])
    """
    start_time = time.time()

    next_turn_my_icetroll_list = predict_next_turn_my_ice_trolls(game)
    next_turn_enemy_icetroll_list = predict_next_turn_enemy_ice_trolls(game)

    # adding new ice trolls

    next_turn_new_ice_trolls = predict_next_turn_new_ice_trolls(game)
    next_turn_my_icetroll_list += next_turn_new_ice_trolls[0]
    next_turn_enemy_icetroll_list += next_turn_new_ice_trolls[1]

    return next_turn_my_icetroll_list, next_turn_enemy_icetroll_list


def predict_next_turn_new_ice_trolls(game):
    """
    This function predict new ice trolls for next turn, the fucntion will return
    all our and the enemy's ice troll that will summon this turn

    :param game:
    :return: the list of new my ice trolls and the list of new enemy ice trolls
    :type: ([IceTroll], [IceTroll)
    """

    next_turn_my_icetroll_list = []
    next_turn_enemy_icetroll_list = []

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

    return next_turn_my_icetroll_list, next_turn_enemy_icetroll_list


def predict_next_turn_my_ice_trolls(game, known_target=False):
    """

    This function predict the locations of my ice trolls for next turn

    :param game:
    :return: the list of new my next turn ice trolls
    :type: [IceTroll]
    """

    next_turn_my_icetroll_list = []

    for my_icetroll in game.get_my_ice_trolls():
        if my_icetroll.current_health == my_icetroll.suffocation_per_turn:  # if the troll is going to die
            continue
        next_turn_my_icetroll = deepcopy_ice_troll(game, my_icetroll)
        next_turn_my_icetroll.current_health -= game.ice_troll_suffocation_per_turn
        if not known_target:
            target = Globals.who_do_i_target.get(my_icetroll)
        else:
            target = known_target
        if target and not can_attack(game, my_icetroll, target):
            next_turn_my_icetroll.location = my_icetroll.get_location().towards(target, game.ice_troll_max_speed)
        next_turn_my_icetroll_list.append(next_turn_my_icetroll)

    return next_turn_my_icetroll_list


def deepcopy_ice_troll(game, ice_troll):
    """

    This function is a faster deepcopy for an ice troll object
    The function just copy the ice troll and deep copy only his location, because his owner, summoner and initial_location
    probably wont change

    :param game:
    :param ice_troll:
    :return: a deep copy of ice_troll
    """

    new_icetroll = copy.copy(ice_troll)
    new_icetroll.location = copy.deepcopy(ice_troll.location)
    return new_icetroll


def predict_next_turn_enemy_ice_trolls(game, known_target=False):
    """

    This function predict the locations of enemy ice trolls for next turn

    :param game:
    :return: the list of new enemy next turn ice trolls
    :type: [IceTroll]
    """

    start_time = time.time()
    next_turn_enemy_icetroll_list = []

    for enemy_icetroll in game.get_enemy_ice_trolls():
        if enemy_icetroll.current_health == enemy_icetroll.suffocation_per_turn:  # if the troll is going to die
            continue
        next_turn_enemy_icetroll = deepcopy_ice_troll(game, enemy_icetroll)
        next_turn_enemy_icetroll.current_health -= game.ice_troll_suffocation_per_turn
        if not known_target:
            target = Globals.who_do_i_target.get(enemy_icetroll)
        else:
            target = known_target

        if target and not can_attack(game, enemy_icetroll, target):
            next_turn_enemy_icetroll.location = enemy_icetroll.get_location().towards(target, game.ice_troll_max_speed)
        next_turn_enemy_icetroll_list.append(next_turn_enemy_icetroll)

    return next_turn_enemy_icetroll_list


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
        if my_lava_giant.current_health == my_lava_giant.suffocation_per_turn:  # if the giant is going to die
            continue
        next_turn_my_lava_giant = copy.deepcopy(my_lava_giant)
        next_turn_my_lava_giant.current_health -= game.lava_giant_suffocation_per_turn
        if not can_attack(game, my_lava_giant, target):
            next_turn_my_lava_giant.location = my_lava_giant.get_location().towards(target, game.lava_giant_max_speed)
        next_turn_my_lava_giant_list.append(next_turn_my_lava_giant)

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

    This function predict the locations of the enemy's elves for next turn by assuming that the enemy elf will move
    towards my closest elf

    :param game:
    :return: a list of next turn enemy's elves with the guessed locations
    :type: [Elf]
    """

    next_turn_enemy_elves_list = []

    for enemy_elf in game.get_enemy_living_elves():
        closest_my_elf = get_closest_my_elf(game, enemy_elf)
        next_turn_enemy_elf = copy.deepcopy(enemy_elf)
        if closest_my_elf.distance(enemy_elf) < game.elf_max_speed:
            next_turn_enemy_elf.location = closest_my_elf.get_location()
        else:
            next_turn_enemy_elf.location = enemy_elf.get_location().towards(closest_my_elf, enemy_elf.max_speed)
        next_turn_enemy_elves_list.append(next_turn_enemy_elf)

    return next_turn_enemy_elves_list


def predict_next_turn_enemy_elves_from_history(game):
    """

    This function predict the locations of the enemy's elves for next turn by he movement from last turn to the current
    turn

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
    DONT USE THIS IS SOME OF ITAMAR'S BS
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


def build(game, elf, building_type_str, loc=False, no_mana_fountains=False):
    """

    This function makes a building with a given elf at a specific location \n If the elf isnt at this position the
    elf will move towards the location safely

    :param game:
    :param elf:
    :param building_type_str:
    :param loc:
    :return:
    """
    start_time = time.time()
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
    print "middle build %s" % (time.time() * 1000 - start_time * 1000)
    if elf.get_location() == loc:
        if building_type_str == MANA_FOUNTAIN or no_mana_fountains or game.get_myself().mana_per_turn > game.default_mana_per_turn:
            if build_dic[building_type_str][0]():  # if elf.can_build_building()
                build_dic[building_type_str][1]()  # then elf.build_building
                print "end build %s" % (time.time() * 1000 - start_time * 1000)
                return True
        print ("Elf %s can't build %s at %s" % (elf, building_type_str, loc))
        print "end build %s" % (time.time() * 1000 - start_time * 1000)
        return False
    else:
        smart_movement(game, elf, loc)
        print "end build %s" % (time.time() * 1000 - start_time * 1000)
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


def check_why_cant_build_building(game, buidling_location, building_radius):
    """

    This function check why an elf cant build a portal in his position.
    The options are amount of mane and buildings in building site

    :param game:
    :param buidling_location:
    :param building_radius:
    :return: if we have enough mana and all buildings in building site
    :type: (Bollean, [Portal/ManaFountain]
    """
    start_time = time.time()
    buildings_in_range = []
    has_mana = False

    for building in get_disturbing_buildings(game, buidling_location, building_radius):
        if building.in_range(buidling_location, 2 * game.portal_size):
            buildings_in_range.append(building)

    if game.get_my_mana() >= game.portal_cost:
        has_mana = True
    else:
        has_mana = False

    why_cant_build_portal = namedtuple("why_cant_build_portal", ["has_mana", "buildings_in_range"])
    print "end check_why_cant_build_building has_mana:%s buildings_in_range: %s time: %s" % (
    has_mana, buildings_in_range, time.time() * 1000 - start_time * 1000)
    return why_cant_build_portal(has_mana, buildings_in_range)


def get_dangerous_enemy_lava_giant(game):
    """

    This function get all dangerous enemy lava giant which mean they are close enough to do significant to my castle
    The function will include the damage that the lava_giant will get this turn

    :param game:
    :return: a list of all the dangerous enemy's lava giants
    :type: [LavaGiant]
    """
    start_time = time.time()
    close_enough_enemy_lava_giant = []

    for lava_giant in game.get_enemy_lava_giants():
        """if len(close_enough_enemy_lava_giant) > 3:
            break"""
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
    print "dangerous enemy lava giants time: %s" % (time.time() * 1000 - start_time * 1000)
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
    # print "get_my_unit_next_turn_health"
    next_turn_hp = my_unit.current_health
    ice_trolls_that_target_me = is_targeted_by_enemy_icetroll(game, my_unit)
    if isinstance(my_unit, Creature):
        next_turn_hp -= my_unit.suffocation_per_turn

    for close_ice_troll in ice_trolls_that_target_me:
        if can_attack(game, close_ice_troll, my_unit):
            next_turn_hp -= game.ice_troll_attack_multiplier

    if include_elves and is_enemy_elf_attacking_elves(game):
        for enemy_elf in game.get_enemy_living_elves():
            if enemy_elf.in_attack_range(my_unit):
                next_turn_hp -= game.elf_attack_multiplier
    # print "get_my_unit_next_turn_healthtime: %s", (time.time()*1000-start_time*1000)
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

    return closest(game, map_object, game.get_enemy_portals() + game.get_enemy_mana_fountains())


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

    # print "in summon_with_closest_portal"
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
    for building in [game.get_my_castle(),
                     game.get_enemy_castle()] + game.get_all_portals() + game.get_all_mana_fountains():
        if building.distance(loc) < radius + building.size:
            disturbing_buildings.append(building)

    return disturbing_buildings


def how_much_hp_in_x_turns(game, game_object, turns=1):
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
                    next_turn_elves = predict_next_turn_enemy_elves_towards(game, enemy_elves_list,
                                                                            get_closest_my_building(game, enemy_elf))
                    if enemy_elf.location.distance() == game.elf_attack_range:
                        health = health - game.elf_attack_multiplier
            i = i - 1
    return health


def does_win_fight(game, elf, attack_target):
    health_dif = elf.current_health
    if (attack_target.type == "Elf" and is_enemy_elf_attacking_elves(game)) or attack_target.type == "IceTroll":
        health_dif -= attack_target.current_health
    elif attack_target.current_health > 50:
        return False
    # print "1health_dif: %s, elf: %s, atattack_target %s" % (health_dif, elf, attack_target)
    for enemy_ice_troll in is_targeted_by_enemy_icetroll(game, elf):
        turns_to_elf = turns_to_travel(game, enemy_ice_troll, elf)
        if turns_to_elf < 5:
            health_dif -= 1 / max(turns_to_elf, 1) * 10
    # print "2health_dif:", health_dif
    for my_ice_troll in is_targeted_by_my_icetroll(game, attack_target):
        turns_to_attack_target = turns_to_travel(game, my_ice_troll, attack_target)
        if turns_to_attack_target < 5:
            health_dif += 1 / max(turns_to_attack_target, 1) * 10
    # print "3health_dif:", health_dif
    for enemy_elf in game.get_enemy_living_elves():
        # print "enemy_elf: %s enemy_elf.distance(elf) %s" % (enemy_elf, enemy_elf.distance(elf))
        if attack_target != enemy_elf and enemy_elf.distance(elf) < game.elf_max_speed + elf.attack_range:
            health_dif -= 1
    # print "4health_dif:", health_dif
    for my_elf in game.get_my_living_elves():
        if elf != my_elf and my_elf.distance(attack_target) < game.elf_max_speed + elf.attack_range:
            health_dif += my_elf.current_health
    # print "health_dif:", health_dif
    if isinstance(attack_target, Building):
        if health_dif > elf.current_health - 1:
            print "will win building"
            return True
    if health_dif < 0:
        return False
    else:
        return True


def is_attack_closest_enemy_portal(game, elf):
    """

    This function check what ever it's would be profitable for a given elf to attack the closest enemy portal to him

    :param game:
    :param elf:
    :return: False if elf shouldn't attack and the object to attack if it's profitable
    """

    closest_enemy_portal = get_closest_enemy_portal(game, elf)
    if not closest_enemy_portal:
        return False

    if elf.in_range(closest_enemy_portal, game.portal_size + game.elf_max_speed + game.elf_attack_range) and \
            does_win_fight(game, elf, closest_enemy_portal):  # , 5 + turns_to_travel(game, elf, closest_enemy_portal)
        return closest_enemy_portal

    return False


def is_attack_closest_enemy_mana_fountain(game, elf):
    """

     This function check what ever it's would be profitable for a given elf to attack the closest enemy mana fountain to
     him

    :param game:
    :param elf:
    :return: False if elf shouldn't attack and the object to attack if it's profitable
    """

    closest_enemy_mana_fountain = get_closest_enemy_mana_fountain(game, elf)
    if not closest_enemy_mana_fountain:
        return False

    if elf.in_range(closest_enemy_mana_fountain,
                    game.mana_fountain_size + game.elf_max_speed + game.elf_attack_range) and \
            does_win_fight(game, elf,
                           closest_enemy_mana_fountain):  # , 5 + turns_to_travel(game, elf, closest_enemy_portal)
        return closest_enemy_mana_fountain

    return False


def is_attack_closest_enemy_elf(game, elf):
    """

    This function check what ever it's would be profitable for a given elf to attack the closest enemy elf to him

    :param game:
    :param elf:
    :return: False if elf shouldn't attack and the object to attack if it's profitable
    """

    closest_enemy_elf = get_closest_enemy_elf(game, elf)
    if not closest_enemy_elf:
        return False

    # print "yuiyui in is_attack_closest_enemy_elf"
    if elf.in_range(closest_enemy_elf, game.portal_size + game.elf_max_speed + game.elf_attack_range) and \
       does_win_fight(game, elf, closest_enemy_elf):  # , 5 + turns_to_travel(game, elf, closest_enemy_portal)
        return closest_enemy_elf

    return False


def attack_closest_enemy_game_obj(game, elves_not_acted):
    """

    attack *close* portals/elves/mana fountains if can win easily

    :param game:
    :param elves_not_acted: a list of all the elves who didn't act all ready
    :return: a list of all the elves who didn't act after the function has ended
    """

    # print "yuiyui in attack_closest_enemy_game_obj, elves_not_acted: %s" % elves_not_acted
    if len(elves_not_acted) > 1:
        for enemy_elf in game.get_enemy_living_elves():
            for my_elf in elves_not_acted:
                if not my_elf.in_attack_range(enemy_elf):
                    break
            else:
                for my_elf in elves_not_acted:
                    attack_object(game, my_elf, enemy_elf)
                return []

    for elf in copy.deepcopy(elves_not_acted):
        does_elf_attack_closest_enemy_portal = is_attack_closest_enemy_portal(game, elf)
        if does_elf_attack_closest_enemy_portal:
            closest_enemy_portal = does_elf_attack_closest_enemy_portal  # is_attack_closest_enemy returns the target
            attack_object(game, elf, closest_enemy_portal)
            print "elf: %s attacking portal: %s" % (elf, closest_enemy_portal)

            Globals.possible_dangerous_enemy_portals[closest_enemy_portal] = []  # the portal isn't dangerous any more
            elves_not_acted.remove(elf)
            continue

        does_elf_attack_closest_enemy_mana_fountain = is_attack_closest_enemy_mana_fountain(game, elf)
        if does_elf_attack_closest_enemy_mana_fountain:
            # is_attack_closest_enemy returns the target
            closest_enemy_mana_fountain = does_elf_attack_closest_enemy_mana_fountain
            attack_object(game, elf, closest_enemy_mana_fountain)
            print "elf: %s attacking mana fountain: %s" % (elf, closest_enemy_mana_fountain)

            elves_not_acted.remove(elf)
            continue

        does_elf_attack_closest_enemy_elf = is_attack_closest_enemy_elf(game, elf)
        # print "yuiyui in for elf: %s does_elf_attack_closest_enemy_elf: %s" % (elf, does_elf_attack_closest_enemy_elf)
        if does_elf_attack_closest_enemy_elf:
            closest_enemy_elf = does_elf_attack_closest_enemy_elf  # is_attack_closest_enemy returns the target
            attack_object(game, elf, closest_enemy_elf)
            print "elf: %s attacking elf: %s" % (elf, closest_enemy_elf)

            elves_not_acted.remove(elf)
            continue

    return elves_not_acted


def is_have_speed_up(game, elf):
    """

    This function check if a given elf have the speed up spell on him.

    :param game:
    :param elf:
    :return: True/False
    """

    if not elf:
        return False

    for spell in elf.current_spells:
        if spell.type == "SpeedUp":
            return True

    return False


def get_invisiblety_spell(game, elf):
    """

    This function gets a given elf invisibility spell if excist

    :param game:
    :param elf:
    :return:
    """

    for spell in elf.current_spells:
        if spell.type == "Invisibility":
            return spell

    return None


def rush_to_loc(game, elf, destination):
    """

    This function rush with a given elf to a given destination

    :param game:
    :param elf:
    :param destination:
    :return:
    """
    print "in rush_to_loc elf: %s, destination: %s" % (elf, destination)
    print "elf.current_spells: %s" % elf.current_spells
    print "elf.can_cast_speed_up(): %s" % elf.can_cast_speed_up()
    print "is_have_speed_up(game, elf):", is_have_speed_up(game, elf)
    if is_have_speed_up(game, elf):
        elf_movement(game, elf, destination)
    elif elf.can_cast_speed_up():
        elf.cast_speed_up()
        print "cast_speed_up"
    else:
        smart_movement(game, elf, destination)


def summon_lava_attack(game, first_arrow_portal):
    """

    if have a lot of mana(the amount depends on the distance of first portal in the arrow to enemy castle).
    then make lava giant with the first portal in the arrow.

    :param game:
    :param first_arrow_portal:
    :return:
    """

    distance_to_castle = first_arrow_portal.distance(game.get_enemy_castle()) - game.portal_size - game.castle_size
    min_mana_to_attack = game.lava_giant_cost * (10 / max(1, game.get_myself().mana_per_turn)) + 20 * (
            distance_to_castle / (game.castle_size + 2 * game.portal_size))
    if game.get_my_mana() > min_mana_to_attack:
        summon_with_closest_portal(game, LAVA, game.get_enemy_castle())


def attack_dangerous_enemy_portals(game, elves_not_acted):
    """

    if there is a enemy portal who is attacking me send an elf to destroy it

    :param game:
    :param elves_not_acted: a list of all the elves who didn't act all ready
    :return: a list of all the elves who didn't actafter the function has ended
    """

    dangerous_enemy_portals = []
    last_summoning_turns_max_length = 3
    arbitrary_number_of_turnes = 15

    for portal, last_summoning_turns in Globals.possible_dangerous_enemy_portals.items():
        if len(last_summoning_turns) == last_summoning_turns_max_length:
            if last_summoning_turns[-1] + arbitrary_number_of_turnes > game.turn:
                dangerous_enemy_portals.append(portal)

    if dangerous_enemy_portals and elves_not_acted:
        print "elves_not_acted", elves_not_acted
        for portal in dangerous_enemy_portals:
            closest_elf_to_portal_loc = closest(game, portal, elves_not_acted)
            if not closest_elf_to_portal_loc or portal.current_health > 50:
                break

            attack_object(game, closest_elf_to_portal_loc, portal)
            print "portal: %s, closest_elf_to_portal_loc: %s" % (portal, closest_elf_to_portal_loc)
            elves_not_acted.remove(closest_elf_to_portal_loc)

    return elves_not_acted

