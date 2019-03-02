
from trainingBot import *
from Attack import *

def get_rush_attack_loc(game):
    print "in get_rush_attack_loc"
    
    
    if game.turn < 23:
        return game.get_enemy_castle()
    
    if game.turn == 23:
        
        enemy_castle = game.get_enemy_castle()
        enemy_mana_fountains = game.get_enemy_mana_fountains()
        enemy_portals = game.get_enemy_portals()
        
        if enemy_mana_fountains:
            closest_mana_fountain_to_castle = closest(game, enemy_castle, enemy_mana_fountains)
            distance_to_castle = closest_mana_fountain_to_castle.distance(enemy_castle)
            if distance_to_castle < game.castle_size + 2 * game.portal_size + 10:
                Globals.rush_attack_loc = closest_mana_fountain_to_castle.get_location()
                return closest_mana_fountain_to_castle.get_location()
        
        elif enemy_portals:
            closest_portal_to_castle = closest(game, enemy_castle, enemy_portals)
            distance_to_castle = closest_portal_to_castle.distance(enemy_castle)
            if distance_to_castle < game.castle_size + 2 * game.portal_size + 10:
                Globals.rush_attack_loc = closest_portal_to_castle.get_location()
                return closest_portal_to_castle.get_location()
        
        Globals.rush_attack_loc = enemy_castle.get_location().towards(Location(0,0), game.castle_size + game.portal_size + 10)
        return enemy_castle.get_location().towards(Location(0,0), game.castle_size + game.portal_size + 10)
    elif non_disdructive_needed_rush_attack_locs(game):
        return closest(game, get_closest_my_elf(game, game.get_enemy_castle()),  non_disdructive_needed_rush_attack_locs(game))
        
    else:
        return Globals.rush_attack_loc
        

def non_disdructive_needed_rush_attack_locs(game):
    
    """
    
    """
    
    possible_locations = []
    dodge_easy = does_win_fight(game, get_closest_my_elf(game, game.get_enemy_castle()),  get_closest_enemy_elf(game, game.get_enemy_castle()))
    
    for r in range(game.castle_size+ game.portal_size, game.get_my_castle().distance(game.get_enemy_castle()), 5):
        for Location in get_circle(game, game.get_enemy_castle().get_location(), r):
                if game.can_build_portal_at(Location): 
                    if not game.get_enemy_living_elves() and not game.get_enemy_ice_trolls():
                        possible_locations.append(Location)
                    elif game.get_enemy_living_elves():
                        if turns_to_travel(game, get_closest_enemy_elf(game,Location), Location) > game.portal_building_duration:
                            if game.get_enemy_ice_trolls():
                                if turns_to_travel(game, get_closest_enemy_ice_troll(game,Location), Location) > game.portal_building_duration:
                                    possible_locations.append(Location)
                            else:
                                possible_locations.append(Location)
                        
                        elif dodge_easy:
                            possible_locations.append(Location)
                    
        if possible_locations:
            break
    
    return possible_locations
     
    

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
    establish_base(game, defence_elves, attack_elf)

    rush_portals = get_rush_portals(game)

    # handle attack elf
    if not rush_portals:
        build_rush_portal(game, attack_elf, rush_attack_loc)

    elif non_disdructive_needed_rush_attack_locs(game):
        build_rush_portal(game, attack_elf, get_rush_attack_loc(game))
    else:
        defend_rush_portals(game, attack_elf)
        defend_from_enemy_elves(game, 3, 4)
    for i in range(0,len(rush_portals),1):
        summon_lava_attack(game, rush_portals[i])


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
        if elf.get_location() == rush_attack_loc:
            if is_safe(game, elf, 3):
                build(game, elf, PORTAL, rush_attack_loc, no_mana_fountains=True)
                print "attack elf %s building portal at: %s" % (elf, rush_attack_loc)
            
            else:
                smart_movement(game, elf, rush_attack_loc.get_location())
                print "attack elf %s running away" % (elf)
        else:
            sneak_movement(game, elf, rush_attack_loc)
    
    else:  # there are disturbing buildings
        closest_building_in_range = closest(game, elf, buildings_in_range)
        if elf.in_attack_range(game.get_enemy_castle()):
            elf.attack(game.get_enemy_castle())
        elif elf.in_attack_range(closest_building_in_range):
            if is_safe(game, elf) or does_win_fight(game, elf, closest_building_in_range):
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
    """elf = attack_closest_enemy_game_obj(game, [elf])
    if elf:
        elf = elf[0]
    else:
        return"""
    
    closest_enemy_elf = get_closest_enemy_elf(game, elf)
    if closest_enemy_elf and turns_to_travel(game, elf, closest_enemy_elf) < 10:
        print "get_closest_my_portal(game, elf)", get_closest_my_portal(game, elf)
        print "closest_enemy_elf.distance(get_closest_my_portal(game, elf))", closest_enemy_elf.distance(get_closest_my_portal(game, elf))
        print "closest_enemy_elf.in_range(get_closest_my_portal(game, elf), elf.max_speed + elf.attack_range +  game.portal_size) %s" % closest_enemy_elf.in_range(get_closest_my_portal(game, elf),  game.portal_size+ elf.max_speed + elf.attack_range)
        if elf.in_attack_range(closest_enemy_elf) or closest_enemy_elf.in_range(get_closest_my_portal(game, elf), elf.max_speed + elf.attack_range+ game.portal_size):
            
            if does_win_fight(game, elf, closest_enemy_elf) or closest_enemy_elf.in_range(get_closest_my_portal(game, elf), elf.max_speed + elf.attack_range+ game.portal_size):
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
                print "elf %s attacking building:%s" % (elf, closest_enemy_building)
                return
            
        smart_movement(game, elf, closest_enemy_building.get_location())
        print "elf %s moving towards building:%s" % (elf, closest_enemy_building)
        return


def sneak_movement(game, elf, destination):

    print "in sneak_movement"
    if is_safe(game, elf):
        elf_movement(game, elf, destination)
        print "elf %s normally moving to %s" % (elf, destination)
        return
    else:
        if not is_have_speed_up(game, elf):
            if elf.can_cast_speed_up() and turns_to_travel(game, elf, destination) > 5:
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

    elves_not_acted = attack_dangerous_enemy_portals(game, elves_not_acted)
    elves_not_acted = attack_closest_enemy_game_obj(game, elves_not_acted)
    
    for elf in copy.deepcopy(elves_not_acted):
        closest_enemy_elf = get_closest_enemy_elf(game, elf)
        if closest_enemy_elf:
            if elf.in_attack_range(closest_enemy_elf):
                if does_win_fight(game, elf, closest_enemy_elf):
                    attack_object(game, elf, closest_enemy_elf)
                    print "elf %s attacking enemy elf:%s" % (elf, closest_enemy_elf)
                    return
                else:
                    smart_movement(game, elf, closest_enemy_elf.get_location())
                    print "elf %s moving towards enemy elf:%s" % (elf, closest_enemy_elf)
                    return
    
        closest_enemy_building = get_closest_enemy_building(game, elf)
        if closest_enemy_building:
            if elf.in_attack_range(closest_enemy_building):
                if does_win_fight(game, elf, closest_enemy_building):
                    attack_object(game, elf, closest_enemy_building)
                    print "elf %s attacking building:%s" % (elf, closest_enemy_building)
                    return
                
            smart_movement(game, elf, closest_enemy_building.get_location())
            print "elf %s moving towards building:%s" % (elf, closest_enemy_building)
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
