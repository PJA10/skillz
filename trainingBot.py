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

RISK_AMOUNT = 1
ICE = "ice"
LAVA = "lava"


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

    enemy_units = get_player_units(game, game.get_enemy())
    return closest(game, map_object, enemy_units)


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
        smart_movement(game, elf, map_object)


def handle_defensive_elf(game, elf):
    pass


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
            print("in if in handle_portals")
            if (game.get_my_ice_trolls() is None or len(game.get_my_ice_trolls()) < 3) or game.get_my_mana() > 200:
                summon(game, port_def, ICE)
    if port_atk != None:
        summon(game, port_atk, LAVA)


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
            print check_why_cant_build_portal(game, elf)
            return False
    else:
        smart_movement(game, elf, loc)
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


def turns_to_travel(game, map_object, destination, max_speed, smart = False):
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
            
            if enemy_elf.distance(elf.get_location()) < game.elf_attack_range:  # if enemy elf in range to attack me
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

    print "possible_movment_points: %s\n destination: %s" % (possible_movement_points, destination)
    elf_movement(game, elf, possible_movement_points[0][0])


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

    if elf.distance(destination) <= elf.max_speed:
        possible_movement_points.append([destination, 1])

    optional_danger = next_turn_enemy_icetrolls_list + game.get_enemy_living_elves()
    if optional_danger:
        closest_danger = min(optional_danger, key=lambda danger: danger.distance(elf))
        run_location = elf.get_location().towards(closest_danger, -elf.max_speed)
        if is_in_game_map(game, run_location):
            possible_movement_points.append([run_location, 1])

    return possible_movement_points


def get_closest_friendly_unit(game, map_object):
    """

    This function return the closest friendly unit(creature + elf) to a given map object

    :param map_object: an object on the map in order to find the closest unit to it
    :return: the closest friendly unit to map_object
    :type: Creature/Elf
    """

    my_units = get_player_units(game, game.get_myself())
    return closest(game, map_object, my_units)


def get_closest_friendly_elf(game, map_object):
    """

    This function return the closest friendly elf to a given map object

    :param map_object: an object on the map in order to find the closest elf to it
    :type map_object: MapObject
    :return: the closest friendly elf to map_object
    :type: Elf
    """

    return closest(game, map_object, game.get_my_living_elves())


def get_closest_friendly_creature(game, map_object):
    """

    This function return the closest friendly creature to a given map object

    :param map_object: an object on the map in order to find the closest creature to it
    :return: the closest friendly creature to map_object
    :type: Creature
    """

    return closest(game, map_object, game.get_my_creatures())


def get_closest_friendly_ice_troll(game, map_object):
    """

    This function return the closest friendly ice troll to a given map object

    :param map_object: an object on the map in order to find the closest creature to it
    :return: the closest friendly ice troll to map_object
    :type: creature
    """

    return closest(game, map_object, game.get_my_ice_trolls())


def get_closest_my_portal(game, map_object):
    """

    This function return the closest friendly portal to a given map object

    :param map_object: an object on the map in order to find the closest creature to it
    :return: the closest friendly portal to map_object
    :type: Portal
    """

    return closest(game, map_object, game.get_my_portals())


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
        if my_icetroll.current_health == my_icetroll.suffocation_per_turn: # if the troll is going to die
            continue
        next_turn_my_icetroll = copy.deepcopy(my_icetroll)
        target = get_closest_enemy_unit(game, my_icetroll)
        if target and my_icetroll.distance(target) > my_icetroll.attack_range:
            next_turn_my_icetroll.location = my_icetroll.get_location().towards(target, game.ice_troll_max_speed)
        next_turn_my_icetroll_list.append(next_turn_my_icetroll)

    next_turn_enemy_icetroll_list = []

    for enemy_icetroll in game.get_enemy_ice_trolls():
        if enemy_icetroll.current_health == enemy_icetroll.suffocation_per_turn: # if the troll is going to die
            continue
        next_turn_enemy_icetroll = copy.deepcopy(enemy_icetroll)
        target = get_closest_friendly_unit(game, enemy_icetroll)
        if target and enemy_icetroll.distance(target) > enemy_icetroll.attack_range:
            next_turn_enemy_icetroll.location = enemy_icetroll.get_location().towards(target, game.ice_troll_max_speed)
        next_turn_enemy_icetroll_list.append(next_turn_enemy_icetroll)

    # adding new ice trolls

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

            if new_icetroll.owner == game.get_myself():
                next_turn_my_icetroll_list.append(new_icetroll)
            elif new_icetroll.owner == game.get_enemy():
                next_turn_enemy_icetroll_list.append(new_icetroll)

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
        if my_lava_giant.current_health == my_lava_giant.suffocation_per_turn: # if the giant is going to die
            continue
        next_turn_my_lava_giant = copy.deepcopy(my_lava_giant)
        if my_lava_giant.distance(target) > my_lava_giant.attack_range:
            next_turn_my_lava_giant.location = my_lava_giant.get_location().towards(target, game.lava_giant_max_speed)
        next_turn_my_lava_giant_list.append(next_turn_my_lava_giant)

    next_turn_enemy_lava_giant_list = []
    target = game.get_my_castle()

    for enemy_lava_giant in game.get_enemy_lava_giants():
        if enemy_lava_giant.current_health == enemy_lava_giant.suffocation_per_turn: # if the giant is going to die
            continue
        next_turn_enemy_lava_gian = copy.deepcopy(enemy_lava_giant)
        if enemy_lava_giant.distance(target) > enemy_lava_giant.attack_range:
            next_turn_enemy_lava_gian.location = enemy_lava_giant.get_location().towards(target, game.lava_giant_max_speed)
        next_turn_enemy_lava_giant_list.append(next_turn_enemy_lava_gian)

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

            if new_lava_giant.owner == game.get_myself():
                next_turn_my_lava_giant_list.append(new_lava_giant)
            elif new_lava_giant.owner == game.get_enemy():
                next_turn_enemy_lava_giant_list.append(new_lava_giant)

    return next_turn_my_lava_giant_list, next_turn_enemy_lava_giant_list


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

    print "next_turn_enemy_elves_list: %s" % next_turn_enemy_elves_list
    print "actual enemy's elves: %s" % game.get_enemy_living_elves()
    return next_turn_enemy_elves_list


def attack_closest_unit(game, elf, max_distance=float("inf")):
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
        attack(game, elf, target)
        return True
    else:
        return False


def attack_closest_portal(game, elf, max_distance=float("inf")):
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
        attack(game, elf, target)
        return True
    else:
        return False


def attack_closest_elf(game, elf, max_distance=float("inf")):
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
        attack(game, elf, target)
        return True
    else:
        return False


def attack_closest_creature(game, elf, max_distance=float("inf")):
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
        attack(game, elf, target)
        return True
    else:
        return False


def check_why_cant_build_portal(game, elf):
    """

    This function check why an elf cant build a portal in his position.
    The options are amount of mane, units are in building site and portals in building site

    :param game:
    :param elf:
    :return: if we have enough mana, all units in building site and all portals in building site
    :type: (Bollean,
    """

    units_in_range = []
    portals_in_range = []
    has_mana = False

    for unit in get_player_units(game, game.get_enemy()) + get_player_units(game, game.get_myself()):
        if unit != elf and elf.in_range(unit, game.portal_size):
            units_in_range.append(unit)

    for portal in game.get_all_portals():
        if portal.in_range(elf, 2 * game.portal_size):
            portals_in_range.append(portal)

    if game.get_my_mana() >= game.portal_cost:
        has_mana = True
    else:
        has_mana = False

    why_cant_build_portal = namedtuple("why_cant_build_portal", ["has_mana", "units_in_range", "portals_in_range"])
    return why_cant_build_portal(has_mana, units_in_range, portals_in_range)


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
        turns_to_travel(game, lava_giant, game.get_my_castle().get_location().towards(lava_giant, game.castle_size),
                        game.lava_giant_max_speed)

        curr_health = lava_giant.current_health
        for my_ice_troll in game.get_my_ice_trolls():
            closest_enemy_unit = get_closest_enemy_unit(game, my_ice_troll)
            if closest_enemy_unit == lava_giant and my_ice_troll.distance(lava_giant) < game.ice_troll_attack_range:
                curr_health -= game.ice_troll_attack_multiplier

        hp_left = curr_health - (turns_to_travel * lava_giant.suffocation_per_turn)
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

    last_turn_gmae = Globals.prev_game

    if Globals.is_enemy_elf_attacking:
        return True
    else:
        for curr_turn_enemy_elf in game.get_enemy_living_elves():
            if not has_moved(game, curr_turn_enemy_elf):
                if not curr_turn_enemy_elf.is_building:
                    for last_turn_my_elf in last_turn_gmae.get_my_living_elves():
                        if last_turn_my_elf.distance(curr_turn_enemy_elf) <= game.elf_attack_range:
                            curr_turn_expected_hp = last_turn_my_elf.current_health
                            last_turn_ice_trolls_that_target_my_elf = is_targeted_by_icetroll(last_turn_gmae, last_turn_my_elf)
                            for close_ice_troll in last_turn_ice_trolls_that_target_my_elf:
                                if close_ice_troll.distance(last_turn_my_elf) < game.ice_troll_attack_range:
                                    curr_turn_expected_hp -= game.ice_troll_attack_multiplier

                            curr_turn_my_elf = get_by_unique_id(game, last_turn_my_elf.unique_id)
                            if curr_turn_my_elf.current_health < curr_turn_expected_hp:
                                Globals.is_enemy_elf_attacking = True
                                return True
    return False


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
    qq
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

    return True # the unit has just spawn



def attack_portal(elf, portal):
    """
    qq
    This function order the given elf to go and attack the given portal if not in range the elf will move towards it

    :param: elf, this elf will be ordered to attack the given portal
    :param: portal, this portal will be attacked by the elf (if it's in range)
    :return: noting
    """
    if elf.attack_range <= elf.get_location().distance(portal.get_location()):
        elf.attack(portal)
    else:
        elf.move_to(portal)




def attack_elf(elf, enemy_elf):
    """
    qq
    This function order the given elf to go and attack the given portal if not in range the elf will move towards it

    :param: elf, this elf will be ordered to attack the given enemy elf
    :param: enemy_elf, this elf will be attacked by our elf (if it's in range)
    :return: noting
    """
    if elf.attack_range <= elf.get_location().distance(enemy_elf.get_location()):
        elf.attack(enemy_elf)
    else:
        elf.move_to(enemy_elf)




def build_portal_in_place(elf):
    """
    qq
    This function will order the given elf to build portal in it's location

    :param: elf, this elf will be ordered to build a portal
    :return: noting
    """
    elf.build_portal()



def build_portal(elf, location):
    """
    qq
    This function will order the given elf to build portal in it's location

    :param: elf, this elf will be ordered to build a portal in the given location
    :return: noting
    """
    if elf.location != location:
        elf.move_to(location)
    else:
        elf.build_portal()



def attack_creature(game, elf, creature):
    """
    qq
    This function will order the given elf to build portal in it's location
    :param: elf, this elf will be ordered to attack the given creature
    :param: creature, the elf will be ordered to attack it
    :return: noting
    """
    if not elf.in_attack_range(creature):
        elf.move_to(creature)
    else:
        elf.attack(creature)

