
from trainingBot import *


def get_rush_attack_loc(game):
    print "in get_rush_attack_loc"
    return game.get_enemy_castle().get_location().towards(Location(3200,6347), game.castle_size + game.portal_size + 50)


def rush_strat(game, elves):
    """

    :param game:
    :param elves:
    :return:
    """
    
    if not elves:
        return
    
    elves = copy.deepcopy(elves)
    rush_attack_loc = get_rush_attack_loc(game)
    print "rush_attack_loc: %s:" % rush_attack_loc
    
    # define elves
    attack_elf = closest(game, rush_attack_loc, elves)
    elves.remove(attack_elf)
    defence_elves = elves

    # handle defence_elves
    defence_elves = attack_dangerous_enemy_portals(game, defence_elves)
    establish_base(game, defence_elves, attack_elf)

    rush_portals = get_rush_portals(game)

    # handle attack elf
    if not rush_portals:
        build_rush_portal(game, attack_elf, rush_attack_loc)

    else:
        defend_rush_portals(game, attack_elf)
        summon_lava_attack(game, rush_portals[0])


def build_rush_portal(game, elf, rush_attack_loc):
    """

    :param game:
    :type game: Game
    :param elf:
    :type elf: Elf
    :param rush_attack_loc:
    :return:
    """

    print "in build_rush_portal"
    
    buildings_in_range = check_why_cant_build_building(game, rush_attack_loc, game.portal_size)[1]
    if not buildings_in_range:
        # if can build portal at the wanted loc, go build
        build(game, elf, PORTAL, rush_attack_loc)
    else:  # there are disturbing buildings
        closest_building_in_range = closest(game, elf, buildings_in_range)

        if elf.in_attack_range(closest_building_in_range):
            if is_safe(game, elf):
                attack_object(game, elf, closest_building_in_range)
                print "attack elf %s attacking: %s" % (elf, closest_building_in_range)

            else:
                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                # need to think if this is our best move
                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                smart_movement(game, elf, closest_building_in_range)
                print "attack elf %s running away" % elf
        else:
            sneak_movement(game, elf, closest_building_in_range.get_location().towards(elf, elf.attack_range))
            print "attack elf %s sneak_movement to: %s" % (elf, closest_building_in_range)


def defend_rush_portals(game, elf):
    print "in defend_rush_portals"
    elf = attack_closest_enemy_game_obj(game, [elf])
    if elf:
        elf = elf[0]
    else:
        return
    
    closest_enemy_elf = get_closest_enemy_elf(game, elf)
    if closest_enemy_elf:
        if elf.in_attack_range(closest_enemy_elf):
            if does_win_fight(game, elf, closest_enemy_elf):
                attack_object(game, elf, closest_enemy_elf)
                print "elf %s attacking enemy elf:%s" % (elf, closest_enemy_elf)
                return
            
        smart_movement(game, elf, closest_enemy_elf.get_location())
        print "elf %s moving towards enemy elf:%s" % (elf, closest_enemy_elf)
        return
    
    closest_enemy_building = get_closest_enemy_building(game, elf)
    if closest_enemy_building:
        if elf.in_attack_range(closest_enemy_building):
            if does_win_fight(game, elf, closest_enemy_building):
                attack_object(game, elf, closest_enemy_building)
                print "elf %s attacking enemy elf:%s" % (elf, closest_enemy_building)
                return
            
        smart_movement(game, elf, closest_enemy_building.get_location())
        print "elf %s moving towards enemy elf:%s" % (elf, closest_enemy_building)
        return


def sneak_movement(game, elf, destination):

    print "in sneak_movement"
    if is_safe(game, elf):
        elf_movement(game, elf, destination)
        print "elf %s normally moving to %s" % (elf, destination)
        return
    else:
        if not is_have_speed_up(game, elf):
            if elf.can_cast_speed_up():
                elf.cast_speed_up()
                print "elf %s is casting speed up" % elf
                return

        if not elf.invisible:
            if elf.can_cast_invisibility():
                elf.cast_invisibility()
                print "elf %s is casting invisibility" % elf
                return

        if elf.invisible or is_have_speed_up(game, elf):
            elf_movement(game, elf, destination)
            print "elf %s normally moving to %s" % (elf, destination)
            return
        else:  # elf isn't inves and not speed up
            smart_movement(game, elf, destination)
            elf_movement(game, elf, destination)
            print "elf %s moving safely to %s" % (elf, destination)
            return


def establish_base(game, defence_elves, attack_elf):
    """

    This function establish our base with a given list of elves.\n
    for now this mean's that the elves will move towards the closest enemy elf and will build mana fountain if attack
    elf is far from the enemy castle

    :param game:
    :param defence_elves:
    :param attack_elf:
    :return:
    """

    print "in establish_base"
    elves_not_acted = defence_elves
    if attack_elf and ((attack_elf.distance(game.get_enemy_castle()) > game.get_enemy_castle().distance(game.get_my_castle()) / 2) or 
       game.get_my_mana > game.invisibility_cost + game.speed_up_cost + game.mana_fountain_cost):
        for elf in copy.deepcopy(elves_not_acted):
            if is_safe(game, elf):
                if build(game, elf, MANA_FOUNTAIN):
                    print "elf %s building mana fountain" % elf
                    elves_not_acted.remove(elf)

    elves_not_acted = attack_closest_enemy_game_obj(game, elves_not_acted)

    for elf in copy.deepcopy(elves_not_acted):
        closest_enemy_elf = get_closest_enemy_elf(game, elf)
        if closest_enemy_elf:
            if elf.in_attack_range(closest_enemy_elf):
                if does_win_fight(game, elf, closest_enemy_elf):
                    attack_object(game, elf, closest_enemy_elf)
                    print "elf %s attacking enemy elf:%s" % (elf, closest_enemy_elf)
                    return
                
            smart_movement(game, elf, closest_enemy_elf.get_location())
            print "elf %s moving towards enemy elf:%s" % (elf, closest_enemy_elf)
            return
    
        closest_enemy_building = get_closest_enemy_building(game, elf)
        if closest_enemy_building:
            if elf.in_attack_range(closest_enemy_building):
                if does_win_fight(game, elf, closest_enemy_building):
                    attack_object(game, elf, closest_enemy_building)
                    print "elf %s attacking enemy elf:%s" % (elf, closest_enemy_building)
                    return
                
            smart_movement(game, elf, closest_enemy_building.get_location())
            print "elf %s moving towards enemy elf:%s" % (elf, closest_enemy_building)
            return

    return elves_not_acted


def get_rush_portals(game):
    """

    This function returns the portals which are part of the rush attack

    :param game:
    :return:
    """

    print "in get_rush_portals"
    enemy_castle = game.get_enemy_castle()
    distance_between_castles = game.get_my_castle().distance(enemy_castle)

    return [close_portal for close_portal in game.get_my_portals()
            if close_portal.distance(enemy_castle) < distance_between_castles/4]


def is_safe(game, elf):
    """

    This function check if a given elf is safe, that's mean that he wont get hit from enemy ice trolls or elves in the
    next 2 turns

    :param game:
    :param elf:
    :return:
    """

    print "in safe"
    ice_troll_safe_distance = 2 * game.ice_troll_max_speed + game.ice_troll_attack_range

    for enemy_ice_troll in is_targeted_by_enemy_icetroll(game, elf):
        if enemy_ice_troll.in_range(elf, ice_troll_safe_distance):
            return False

    for enemy_elf in game.get_enemy_living_elves():
        elf_safe_distance = 2 * enemy_elf.max_speed + game.elf_attack_range
        if enemy_elf.in_range(elf, elf_safe_distance):
            return False

    return True

