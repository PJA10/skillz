"""
############
Attack
############
.. module:: Attack

"""

from trainingBot import *
import Globals
from collections import *
import time


def attack(game, elf, attack_dest, **kwargs):
    """

    :param game:
    :type game: Game
    :param elf:
    :type elf: ELf
    :param attack_dest:
    :type attack_dest: MapObject
    :param kwargs:
    :return:
    """
    mana_state, distraction_portals, attacking_portals = Globals.mana_state, \
                                                        Globals.distraction_portals,\
                                                        Globals.attacking_portals
    offset = 5  # turns
    if not kwargs.get("attacking_portal_destination"):
        kwargs["attacking_portal_destination"] = best_attacking_portal_location(game, attack_dest)
        kwargs["turn_limit_for_dest"] = turns_to_travel(game, elf, kwargs["attacking_portal_destination"][0], smart=True)

    attacking_portal_destination, safe_range = kwargs["attacking_portal_destination"]
    turn_limit_for_dest = kwargs["turn_limit_for_dest"]

    if turns_to_travel(game, elf, attacking_portal_destination, smart=True) > turn_limit_for_dest + offset:
        already_acted, change_att_portal_dest = handle_obstacle(game, elf, attacking_portal_destination, safe_range)
        if not already_acted and change_att_portal_dest:
            return attack(game, elf, attack_dest, {})

    # maybe add if the elf is in attacking_portal_destination and not elf.can_build_portal() then handle_obstacle()
    elif not elf.in_range(attacking_portal_destination, safe_range) or not elf.can_build_portal():
        if game.get_my_mana() < game.portal_cost:
            mana_state = "save mana"

        closest_enemy_portal = get_closest_enemy_portal(game, elf)
        closest_enemy_elf = get_closest_enemy_elf(game, elf)

        if get_objects_in_path(game, elf, attacking_portal_destination, [closest_enemy_portal],
                               game.portal_size + game.elf_max_speed + game.elf_attack_range) and \
           does_win_fight(game, elf, closest_enemy_portal):

            attack_object(game, elf, closest_enemy_portal)

        elif get_objects_in_path(game, elf, attacking_portal_destination, [closest_enemy_elf],
                               game.elf_max_speed + game.elf_attack_range) and \
           does_win_fight(game, elf, closest_enemy_elf):
            attack_object(game, elf, closest_enemy_elf)
        else:
            smart_movement(game, elf, attacking_portal_destination)
    elif elf.can_build_portal():
        elf.build_portal()
        attacking_portal_destination = None

    # mana and wave
    some_arbitrary_number = 10  # need to find the right magic number !!!
    wave_strength = determine_wave_strength(game)
    if mana_state == "wave" and wave_strength > some_arbitrary_number:
        attack_wave(game)
    elif wave_strength > some_arbitrary_number * 2:  # again this number needs to change !!!
        attack_wave(game)

    min_amount_of_mana_for_pulse = 70  # again this number needs to change !!!
    if game.get_my_mana() > min_amount_of_mana_for_pulse:
        mana_state == "wave"

    Globals.maana_state = mana_state
    return (attacking_portal_destination, safe_range), turn_limit_for_dest - 1


def attack_wave(game):
    """

    This function attack the enemy with a wave of lava giants.
    The attacking portals will include portals that will do enough damage to the enemy castle.
    If we have enough mana the attack will include distraction(ice trolls) from some of global distraction_portals.

    :param game:
    :type game: Game
    :return:
    """

    # available portals sorted by distance to enemy castle
    attacking_portals = [portal for portal in game.get_my_portals() if not portal.is_summoning]
    attacking_portals = sorted(attacking_portals, key=lambda portal: portal.distance(game.get_enemy_castle()))

    for portal in attacking_portals[:]:  # a copy of attacking_portals
        lava_giant_damage = game.lava_giant_max_health - \
                            (game.lava_giant_suffocation_per_turn *
                             turns_to_travel(game, portal, max_speed=game.lava_giant_max_speed))

        if lava_giant_damage < 0.1 * game.get_enemy_castle().current_helath:
            attacking_portals.remove(portal)  # remove portals which wont do even 10% of the enemy castle hp

    mana_left = game.get_my_mana() > len(attacking_portals) * game.lava_giant_cost
    if mana_left < 0:  # if we don't have a lot of mana, just make lava as mush as we can
        for portal in attacking_portals:
            if portal.can_summon_lava_giant():
                portal.summon_lava_giant()
    else:
        if mana_left > game.ice_troll_cost:  # if we have a lot of mana
            if Globals.distraction_portals:
                #  check how many distractions we can make
                this_wave_distraction_portals = []
                for distraction_portal in Globals.distraction_portals:
                    mana_left = mana_left + game.lava_giant_cost - game.ice_troll_cost
                    if mana_left < 0:
                        break
                    this_wave_distraction_portals.append(distraction_portal)
                    attacking_portals.remove(distraction_portal)

                # summon
                for attack_portal in attacking_portals:
                    summon(game, attack_portal, LAVA)
                for distraction_portal in this_wave_distraction_portals:
                    summon(game, distraction_portal, ICE)


def determine_wave_strength(game):
    """

    This function determine what will be the strength of a pule if one will be made
    The function takes in matter the damage that will be done by lava giants that will be spawn by available portals
    The function also takes in matter the number of enemy's defensive portals, ice trolls and elves

    :param game:
    :return: a number representing the strength of a pulse if one will be made
    :type: Int
    """

    number_of_possible_ice_trolls = game.get_my_mana() / game.ice_troll_cost
    my_available_portals = [portal for portal in game.get_my_portals() if not portal.is_summoning]
    my_available_portals = sorted(my_available_portals, key=lambda portal: portal.distance(game.get_enemy_castle()))

    total_lava_giant_damage = 0
    attack_portals = my_available_portals[slice(number_of_possible_ice_trolls)]
    for portal in attack_portals:
        lava_giant_damage = game.lava_giant_max_health -\
                            (game.lava_giant_suffocation_per_turn *
                             turns_to_travel(game, portal, game.get_enemy_castle(), max_speed=game.lava_giant_max_speed))

        total_lava_giant_damage += lava_giant_damage

    enemy_defence_strength = determine_enemy_defense_strength(game, attack_portals)
    return total_lava_giant_damage - enemy_defence_strength


def determine_enemy_defense_strength(game, attack_portals):
    """

    This function determine the strength of the enemy's defense
    he function takes in matter the number of enemy's defensive portals, ice trolls and elves

    :param game:
    :type game: Game
    :param attack_portals: my portals which will attack
    :type attack_portals: [Portal]
    :return: a number representing the strength of the enemy's defense
    :type: Int
    """

    strength = 0
    enemy_castle = game.get_enemy_castle()

    strength += game.get_enemy_mana() / (game.ice_troll_cost * 1.5)  # enemy amount of mana

    # enemy amount of ice_troll
    strength += len([ice_troll for ice_troll in game.get_enemy_ice_trolls() if
                   ice_troll.current_helath > game.lava_giant_summoning_duration * game.ice_troll_suffocation_per_turn])

    # amount of portals
    farthest_my_portal_to_enemy_castle = closest(game, game.get_my_castle(), attack_portals)
    strength += len([portal for portal in game.get_enemy_portals()
                    if portal.distance(game.enemy_castle) <
                    farthest_my_portal_to_enemy_castle.distance(game.enemy_castle)])

    # amount of ice trolls in production
    strength += len([portal for portal in game.get_enemy_portals() if
                     portal.is_summoning and portal.currently_summoning == "IceTroll"])

    # elves
    strength += len([elf for elf in game.get_enemy_living_elves() if
                     elf.distance(game.enemy_castle) < farthest_my_portal_to_enemy_castle.distance(game.enemy_castle)
                     and elf.turns_to_build <= 3])

    return strength


def handle_obstacle(game, elf, attacking_portal_destination, safe_range):
    """

    This function handle obstacles that are disturbing elf to build an attacking portal
    The function will identify the obstacle and act correctly

    :param game:
    :type game: Game
    :param elf:
    :type elf: Elf
    :param attacking_portal_destination:
    :type attacking_portal_destination: Location
    :param safe_range:
    :type safe_range: Int
    :return:
    """

    already_acted, change_att_portal_dest = False, False

    if elf.in_range(attacking_portal_destination, safe_range):
        if not elf.can_build_portal():
            has_mana, portals_in_range = check_why_cant_build_portal(game, elf)
            if portals_in_range:
                already_acted = attack_closest_enemy_portal(game, elf), False
            elif not has_mana:
                Globals.mana_state = "save mana"
                already_acted = False
        else:  # false alarm
            elf.build_portal()
            already_acted = True
    else:  # cant get to attacking_portal_destination
        # probably elf or ice trolls are in the way

        elves_in_the_path = get_objects_in_path(game, elf, attacking_portal_destination, game.get_enemy_living_elves())
        ice_trolls_in_the_path = get_objects_in_path(game, elf, attacking_portal_destination, game.get_enemy_ice_trolls())

        if not elves_in_the_path and not ice_trolls_in_the_path:
            # there are no elves and no ice trolls
            # then just change attack portal dest
            change_att_portal_dest = True

        # if elf is in the way, fight him if we will win and choose new attacking_portal_destination if will lose
        elif len(elves_in_the_path) == 1:
            if does_win_fight(game, elf, elves_in_the_path[0]):
                attack_object(game, elf, elves_in_the_path[0])
                already_acted = True
            else:
                change_att_portal_dest = True

        elif len(elves_in_the_path) > 1:
            change_att_portal_dest = True

        # if ice_troll is in the way, if there is only one add time, else choose new attacking_portal_destination
        elif len(ice_trolls_in_the_path) != 1:
            change_att_portal_dest = True

    return already_acted, change_att_portal_dest


def best_attacking_portal_location(game, attack_dest):
    """

    :param game:
    :param attack_dest:
    :return:
    :type: (x, y)
    """
    pass  # eyal's


def does_win_fight_v1(game, elf, attack_target, max_depth=4):
    """

    The function calculate who will win if *elf* and *attack_target* will start a fight this turn
    The function thinks to the next *max_depth* turns what will happen with close ice trolls

    :param game:
    :param elf: the elf to start a fight with
    :param attack_target: the elf's target
    :type attack_target: MapObject
    :param max_depth: the max number of turns to calculate. take care of running time!!
    :return: if elf is going to win or not
    :type: Boolean
    """

    curr_elf = copy.deepcopy(elf)
    curr_attack_target = copy.deepcopy(attack_target)
    curr_game = copy.deepcopy(game)
    curr_turn = 0

    print "elf: %s, attack_target %s, max_depth: %s" % (elf, attack_target, max_depth)
    start_time = time.time()
    # loop over the next turns until elf or attack_target will die
    while curr_attack_target.current_health and curr_elf.current_health  and curr_turn < max_depth:
        print "----------%s---------%s" % ( curr_turn, time.time()*1000-start_time*1000)

        print "enemy_ice_trolls: %s" % curr_game.get_enemy_ice_trolls()
        # print ",".join(str((portal, portal.turns_to_summon)) for portal in curr_game.get_enemy_portals())

        elf_next_turn_hp = get_my_unit_next_turn_health(curr_game, curr_elf, include_elves=True)
        print "between players"
        attack_target_next_turn_hp = get_enemy_unit_next_turn_health(curr_game, curr_attack_target, True)
        print "curr_elf hp: %s, elf_next_turn_hp %s" % (curr_elf.current_health, elf_next_turn_hp)
        print "curr_attack_target hp: %s, curr_attack_target %s, time:%s" % (curr_attack_target.current_health, attack_target_next_turn_hp, time.time()*1000-start_time*1000)

        if not curr_elf.in_attack_range(attack_target):
            curr_elf.location = curr_elf.get_location().towards(attack_target, game.elf_max_speed)


        next_turn_my_ice_trolls, next_turn_enemy_ice_trolls = predict_next_turn_ice_trolls(curr_game)
        print "does win fight time: %s", (time.time()*1000-start_time*1000)
        curr_game.get_myself().ice_trolls = next_turn_my_ice_trolls
        # print "next_turn_enemy_ice_trolls", next_turn_enemy_ice_trolls
        curr_game.get_enemy().ice_trolls = next_turn_enemy_ice_trolls
        curr_elf.current_health = elf_next_turn_hp
        curr_attack_target.current_health = attack_target_next_turn_hp
        for portal in curr_game.get_all_portals():
            if portal.is_summoning:
                portal.turns_to_summon -= 1
            if portal.turns_to_summon == 0:
                portal.is_summoning = False
        curr_turn += 1

    if curr_elf.current_health > curr_attack_target.current_health:  # if we will  won
        print "will win"
        return True
    else:  # if we lost or draw
        print "will lose"
        return False


def does_win_fight(game, elf, attack_target):

    health_dif = 0
    if attack_target.type == "Elf" or attack_target.type == "IceTroll" or attack_target.type == "LavaGiant":
        health_dif = attack_target.current_health - elf.current_health
    health_dif -= len([ice_troll for ice_troll in is_targeted_by_enemy_icetroll(game, elf)
                       if ice_troll.in_range(elf, game.ice_troll_max_speed*2 + game.ice_troll_attack_range)])
    health_dif += len([ice_troll for ice_troll in is_targeted_by_my_icetroll(game, attack_target)
                       if ice_troll.in_range(attack_target, game.ice_troll_max_speed*2 + game.ice_troll_attack_range)])
    if health_dif < 0:
        return False
    else:
        return True


def defend_from_enemy_elves(game, elves_not_acted, max_number_of_icetrolls_on_unit):
    """

    if there is a close elf to one of our portals, summon ice from a close portal.

    :param game:
    :param elves_not_acted: a list of all the elves who didn't act all ready.
    :param max_number_of_icetrolls_on_unit: the max number of ice trolls on one unit
    :return: a list of all the elves who didn't act all ready after the function has ended
    """

    prev_game = Globals.prev_game

    for portal in game.get_my_portals():
        """ # defend from all enemy elves that come towards portal
        for last_turn_enemy_elf in prev_game.get_enemy_living_elves():
            enemy_elf = get_by_unique_id(game, last_turn_enemy_elf.unique_id)
            if not enemy_elf:
                continue
            if len(is_targeted_by_my_icetroll(game, enemy_elf)) > max_number_of_icetrolls_on_unit:
                continue

            if last_turn_enemy_elf.get_location().towards(portal, game.elf_max_speed) == enemy_elf.get_location():
                summon_with_closest_portal(game, ICE, portal)
        """
        for enemy_elf in game.get_enemy_living_elves():
            if len(is_targeted_by_my_icetroll(game, enemy_elf)) > max_number_of_icetrolls_on_unit:
                continue

            curr_enemy_elf_distance = enemy_elf.distance(portal)
            prev_enemy_elf = get_by_unique_id(prev_game, enemy_elf.unique_id)
            if prev_enemy_elf:
                prev_enemy_elf_distance = prev_enemy_elf.distance(portal)
                if prev_enemy_elf_distance > curr_enemy_elf_distance:  # if the enemy elf is running away from portal
                    continue

            attacking_pos = portal.get_location().towards(enemy_elf, game.portal_size + game.elf_attack_range)
            if turns_to_travel(game, enemy_elf, attacking_pos) < 5 and not is_targeted_by_my_icetroll(game, enemy_elf):
                summon_with_closest_portal(game, ICE, portal)
                print "summon ice, close elf"

        if game.get_my_mana() >= game.ice_troll_cost:
            for lava_giant in get_dangerous_enemy_lava_giant(game):
                if game.get_my_mana() < game.ice_troll_cost:
                    break

                if len(is_targeted_by_my_icetroll(game, lava_giant)) > max_number_of_icetrolls_on_unit:
                    continue
                max_distance = 3000
                if game.get_enemy_portals():
                    max_distance = game.get_my_castle().distance(get_closest_enemy_portal(game, game.get_my_castle()))
                if len(in_object_range(game, game.get_my_castle(), game.get_my_ice_trolls(), max_distance)) > max_number_of_ice_trolls_near_base:
                    continue
                if turns_to_travel(game, lava_giant, game.get_my_castle(), game.lava_giant_max_speed) <=6 and not is_targeted_by_my_icetroll(game, lava_giant):
                    spawn_turn_lava_giant_loc = lava_giant.get_location().towards(game.get_my_castle(), game.lava_giant_max_speed *
                                                                          game.ice_troll_summoning_duration)
                    summon_with_closest_portal(game, ICE, spawn_turn_lava_giant_loc)
                    print "summon ice. defend from lava"
    # elf handling

    return elves_not_acted


def defend_from_enemy_lava_giants(game, elves_not_acted, max_number_of_icetrolls_on_unit,
                                  max_number_of_ice_trolls_near_base):
    """

    if there are dangerous enemy lava giants summon ice from a portal close to the lava giants location three turns from now.

    :param game:
    :param elves_not_acted: a list of all the elves who didn't act all ready.
    :param max_number_of_icetrolls_on_unit: the max number of ice trolls on one unit
    :param max_number_of_ice_trolls_near_base: the max number of ice trolls near base
    :return: a list of all the elves who didn't act all ready after the function has ended
    """

    arbitrary_number_of_turns = 6

    if game.get_my_mana() >= game.ice_troll_cost:
        for lava_giant in get_dangerous_enemy_lava_giant(game):
            if game.get_my_mana() < game.ice_troll_cost:
                break

            if len(is_targeted_by_my_icetroll(game, lava_giant)) > max_number_of_icetrolls_on_unit:
                continue
            max_distance = 3000
            if game.get_enemy_portals():
                max_distance = game.get_my_castle().distance(get_closest_enemy_portal(game, game.get_my_castle()))
            if len(in_object_range(game, game.get_my_castle(), game.get_my_ice_trolls(),
                                   max_distance)) > max_number_of_ice_trolls_near_base:
                continue
            num_of_turnes_to_my_castle = turns_to_travel(game, lava_giant, game.get_my_castle(),
                                                         game.lava_giant_max_speed)

            if num_of_turnes_to_my_castle <= arbitrary_number_of_turns and \
                    not is_targeted_by_my_icetroll(game, lava_giant):
                spawn_turn_lava_giant_loc = lava_giant.get_location().towards(game.get_my_castle(),
                                                                              game.lava_giant_max_speed *
                                                                              game.ice_troll_summoning_duration)
                summon_with_closest_portal(game, ICE, spawn_turn_lava_giant_loc)
                print "summon ice. defend from lava"

    return elves_not_acted


def arrow_def(game, elves_not_acted):
    """

    defence:\n
    * if there is a close elf to one of our portals, summon ice.
    * if there are dangerous enemy lava giants summon ice from a portal close to the lava giants location three turns from now.
    * if there is a enemy portal who is attacking me send an elf to destroy it

    :param game:
    :param elves_not_acted: a list of all the elves who didnt act all ready
    :return: a list of all the elves who didn't act all ready after the function has ended
    """

    max_number_of_icetrolls_on_unit = 1
    max_number_of_ice_trolls_near_base = 3

    if game.get_my_castle().current_health < game.get_enemy_castle().current_health:
        max_number_of_ice_trolls_near_base += 1

    elves_not_acted = defend_from_enemy_elves(game, elves_not_acted, max_number_of_icetrolls_on_unit)

    elves_not_acted = defend_from_enemy_lava_giants(game, elves_not_acted, max_number_of_icetrolls_on_unit,
                                                    max_number_of_ice_trolls_near_base)

    elves_not_acted = attack_dangerous_enemy_portals(game, elves_not_acted)

    return elves_not_acted


def attack_dangerous_enemy_portals(game, elves_not_acted):
    """

    if there is a enemy portal who is attacking me send an elf to destroy it

    :param game:
    :param elves_not_acted: a list of all the elves who didn't act all ready
    :return: a list of all the elves who didn't act all ready after the function has ended
    """


    dangerous_enemy_portals = []
    last_summoning_turns_max_length = 3
    arbitrary_number_of_turnes = 15

    for portal, last_summoning_turns in Globals.possible_dangerous_enemy_portals.items():
        if len(last_summoning_turns) == last_summoning_turns_max_length:
            if last_summoning_turns[-1] + arbitrary_number_of_turnes > game.turn:
                dangerous_enemy_portals.append(portal)

    if dangerous_enemy_portals and elves_not_acted:
        print "elf_not_acted", elves_not_acted
        for portal in dangerous_enemy_portals:
            closest_elf_to_portal_loc = closest(game, portal, elves_not_acted)
            if not closest_elf_to_portal_loc:
                break
            attack_object(game, closest_elf_to_portal_loc, portal)
            print "portal: %s, closest_elf_to_portal_loc: %s" % (portal, closest_elf_to_portal_loc)
            elves_not_acted.remove(closest_elf_to_portal_loc)

    return elves_not_acted


def attack_closest_enemy_game_obj(game, elves_not_acted, arrow_next_portal_loc):
    """

    attack close portals/elves if can win easily

    :param game:
    :param elves_not_acted: a list of all the elves who didn't act all ready
    :param arrow_next_portal_loc:
    :return: a list of all the elves who didn't act all ready after the function has ended
    """

    for elf in copy.deepcopy(elves_not_acted):
        # attack close enemy objects
        closest_enemy_portal = get_closest_enemy_portal(game, elf)
        closest_enemy_elf = get_closest_enemy_elf(game, elf)

        if closest_enemy_portal and elf.in_range(closest_enemy_portal,
                                                 game.portal_size + game.elf_max_speed + game.elf_attack_range) and \
                does_win_fight(game, elf,
                               closest_enemy_portal):  # , 5 + turns_to_travel(game, elf, closest_enemy_portal)

            attack_object(game, elf, closest_enemy_portal)
            print "elf: %s attacking: %s" % (elf, closest_enemy_portal)
            elves_not_acted.remove(elf)
            continue

        if closest_enemy_elf and elf.in_range(closest_enemy_elf,
                                              game.portal_size + game.elf_max_speed + game.elf_attack_range) and \
                does_win_fight(game, elf, closest_enemy_elf):  # , 5 + turns_to_travel(game, elf, closest_enemy_portal)

            attack_object(game, elf, closest_enemy_elf)
            print "elf: %s attacking: %s" % (elf, closest_enemy_elf)
            elves_not_acted.remove(elf)
            continue

    return elves_not_acted


def build_next_arrow_portal(game, elves_not_acted, arrow_next_portal_loc, first_arrow_portal):
    """

    * if can continue arrow without problems, continue (no enemy portals in the way).
    * elif can easily destroy closest disturbing enemy portals, then do.
    * elif have enough mana, get cover by ice trolls and destroy closest disturbing enemy portals.
    * else mana state = "save mana" and defend current arrow (maybe attack ice trolls).

    :param game:
    :param elves_not_acted:
    :param first_arrow_portal:
    :return: a list of all the elves who didn't act all ready after the function has ended, and mana state
    :type: ([Elf], str)
    """

    disturbing_enemy_portals = get_objects_in_path(game, arrow_next_portal_loc, first_arrow_portal,
                                                   game.get_enemy_portals(), game.portal_size * 2)
    closest_elf_to_portal_loc = closest(game, arrow_next_portal_loc, elves_not_acted)

    if closest_elf_to_portal_loc:
        if not disturbing_enemy_portals:
            if make_portal(game, closest_elf_to_portal_loc, arrow_next_portal_loc):
                if closest_elf_to_portal_loc.is_building:  # if the elf is building the portal
                    Globals.arrow_next_portal_loc = None
                else:  # if the elf is going to the portal location
                    turns_to_dis = turns_to_travel(game, closest_elf_to_portal_loc, arrow_next_portal_loc)
                    mana_at_arrival = game.get_my_mana() + turns_to_dis * game.default_mana_per_turn
                    if mana_at_arrival < game.portal_cost:
                        mana_state = "save mana"

                elves_not_acted.remove(closest_elf_to_portal_loc)
                print "elf %s making portal at: %s" % (closest_elf_to_portal_loc, arrow_next_portal_loc)
            else:  # the elf cant build the portal
                has_mana, portals_in_range = check_why_cant_build_portal(game, closest_elf_to_portal_loc)
                if portals_in_range:
                    disturbing_enemy_portals.extend(portals_in_range)

                if not has_mana:
                    mana_state = "save_mana"

        if disturbing_enemy_portals:
            closest_disturbing_portal = closest(game, closest_elf_to_portal_loc, disturbing_enemy_portals)
            turns_to_disturbing_portal = turns_to_travel(game, closest_elf_to_portal_loc, closest_disturbing_portal)
            if does_win_fight(game, closest_elf_to_portal_loc, closest_disturbing_portal):
                attack_object(game, closest_elf_to_portal_loc, closest_disturbing_portal)
                print "elf: %s attacking closest_disturbing_portal: %s" % (
                    closest_elf_to_portal_loc, closest_disturbing_portal)
                elves_not_acted.remove(closest_elf_to_portal_loc)

            elif game.get_my_mana() > game.ice_troll_cost:  # if we don't win the fight, get help
                summon(game, first_arrow_portal, ICE)
                attack_object(game, closest_elf_to_portal_loc, closest_disturbing_portal)
                print "elf: %s attacking closest_disturbing_portal: %s" % (
                    closest_elf_to_portal_loc, closest_disturbing_portal)
                elves_not_acted.remove(closest_elf_to_portal_loc)

            else:
                mana_state = "save mana"
                smart_movement(game, closest_elf_to_portal_loc, closest_elf_to_portal_loc.get_location())
                print "elf %s running away" % closest_elf_to_portal_loc
                elves_not_acted.remove(closest_elf_to_portal_loc)
                # need to add: defend current arrow (maybe attack ice trolls)

    return elves_not_acted, mana_state


def arrow_attack(game, elves_not_acted):
    """

    attack close portals/elves if can win easily\n

    build arrow of portals:\n
    * if can continue arrow without problems, continue (no enemy portals in the way).
    * elif can easily destroy closest disturbing enemy portals, then do.
    * elif have enough mana, get cover by ice trolls and destroy closest disturbing enemy portals.
    * else mana state = "save mana" and defend current arrow (maybe attack ice trolls).

    if mana state = "attack" and have a lot of mana(the amount depends on the distance of first portal in the arrow to enemy castle).
    then make lava giant with the first portal in the arrow.

    :param game:
    :param elves_not_acted:
    :return:
    """

    prev_game = Globals.prev_game
    arrow_next_portal_loc = get_next_arrow_portal_loc(game)

    attack_closest_enemy_game_obj(game, elves_not_acted, arrow_next_portal_loc)

    # build arrow
    first_arrow_portal = closest(game, game.get_enemy_castle(), game.get_my_portals() + [game.get_my_castle()])

    elves_not_acted, mana_state = build_next_arrow_portal(game, elves_not_acted, first_arrow_portal)

    if elves_not_acted:
        for elf in elves_not_acted:
            closest_enemy_portal = get_closest_enemy_portal(game, elf)
            if closest_enemy_portal:
                print "elf %s is attacking : %s" % (elf, closest_enemy_portal)
                attack_object(game, elf, closest_enemy_portal)
                continue

            closest_enemy_unit = get_closest_enemy_unit(game, elf)
            if closest_enemy_unit:
                print "elf %s is attacking : %s" % (elf, closest_enemy_unit)
                attack_object(game, elf, closest_enemy_unit)
                continue

            smart_movement(game, elf, elf.get_location())  # stay in place

    if mana_state == "attack":
        summon_lava_attack(game, first_arrow_portal)


def summon_lava_attack(game, first_arrow_portal):
    """

    if have a lot of mana(the amount depends on the distance of first portal in the arrow to enemy castle).
    then make lava giant with the first portal in the arrow.

    :param game:
    :param first_arrow_portal:
    :return:
    """

    distance_to_castle = first_arrow_portal.distance(game.get_enemy_castle()) - game.portal_size - game.castle_size
    print "distance_to_castle", distance_to_castle
    min_mana_to_attack = game.lava_giant_cost + 20 * (distance_to_castle / (game.castle_size + 2 * game.portal_size))
    print "min_mana_to_attack", min_mana_to_attack
    if game.get_my_mana() > min_mana_to_attack:
        summon_with_closest_portal(game, LAVA, game.get_enemy_castle())


def arrow_strategy(game):
    """

    defence:\n
    * if there is a close elf to one of our portals, summon ice.
    * if there are dangerous enemy lava giants summon ice from a portal close to the lava giants location three turns from now.
    * if there is a enemy portal who is attacking me send an elf to destroy it

    attack close portals/elves if can win easily\n

    build arrow of portals:\n
    * if can continue arrow without problems, continue (no enemy portals in the way).
    * elif can easily destroy closest disturbing enemy portals, then do.
    * elif have enough mana, get cover by ice trolls and destroy closest disturbing enemy portals.
    * else mana state = "save mana" and defend current arrow (maybe attack ice trolls).

    if mana state = "attack" and have a lot of mana(the amount depends on the distance of first portal in the arrow to enemy castle).
    then make lava giant with the first portal in the arrow.

    :param game:
    :type game: Game
    :return:
    """

    mana_state = "attack"
    prev_game = Globals.prev_game
    elf_not_acted = copy.deepcopy(game.get_my_living_elves())

    elf_not_acted = arrow_def(game, elf_not_acted)

    arrow_attack(game, elf_not_acted)


def get_next_arrow_portal_loc(game):
    """

    This function get the next location for a portal in the arrow attack

    :param game:
    :type game: Game
    :return: the location of the next location for a portal in the arrow attack
    :type: Location
    """


    portals =  get_objects_in_path(game, game.get_my_castle(), game.get_enemy_castle(), game.get_my_portals()) + [game.get_my_castle().get_location().towards(game.get_enemy_castle(), 10)]
    for elf in game.get_my_living_elves():
        if elf.is_building:
            portals.append(elf.get_location())
    first_portal = closest(game, game.get_enemy_castle(), portals)
    print "first_portal:", first_portal
    return first_portal.get_location().towards(game.get_enemy_castle(), game.castle_size + game.portal_size)
    if Globals.arrow_next_portal_loc and game.get_my_portals() == Globals.prev_game.get_my_portals():
        return Globals.arrow_next_portal_loc
    else:
        portals = get_objects_in_path(game, game.get_my_castle(), game.get_enemy_castle(), game.get_my_portals()) + \
                  [game.get_my_castle().get_location().towards(game.get_enemy_castle(), 10)]
        for elf in game.get_my_living_elves():
            if elf.is_building:
                portals.append(elf.get_location())
        first_portal = closest(game, game.get_enemy_castle(), portals)
        print "first_portal:", first_portal
        Globals.arrow_next_portal_loc = first_portal.get_location().towards(game.get_enemy_castle(),
                                                                            game.castle_size + game.portal_size)
        return Globals.arrow_next_portal_loc


def attacks_close_to_our_castle_portals(game, elves_not_acted, first_arrow_portal):
    """

    This function checks if an enemy elf starts creating a portal close to us,
    if he is elf and ice troll will be send to attack him and the portal
    if there is a dangerous enemy portal an elf will be send to destroy it

    :return: nothing
    """
    my_castle = game.get_my_castle()
    if elves_not_acted:
        if game.get_enemy_living_elves():
            if game.get_enemy_portals():
                for enemy_portal in game.get_enemy_portals():
                    closest_my_elf = closest(game, enemy_portal, elves_not_acted)
                    closest_ENEMY_elf = get_closest_enemy_elf(game, enemy_portal)
                    if enemy_portal.distance(my_castle) < first_arrow_portal.distance(my_castle):
                        if does_win_fight(game, closest_my_elf, enemy_portal):
                            if not closest_my_elf.in_attack_range(closest_ENEMY_elf):
                                attack_object(game, closest_my_elf, enemy_portal)
                                print "elf %s is attacking : %s" % (closest_my_elf, closest_ENEMY_elf)

                            elif does_win_fight(game, closest_my_elf, closest_ENEMY_elf):
                                attack_object(game, closest_my_elf, closest_ENEMY_elf)
                                print "elf %s is attacking : %s" % (closest_my_elf, closest_ENEMY_elf)

                            else:
                                smart_movement(game, closest_my_elf, closest_ENEMY_elf.get_location())
                                print "elf %s is moving to : %s" % (closest_my_elf, closest_ENEMY_elf.get_location())

                        else:
                            if turns_to_travel(game, get_closest_my_portal(game, closest_ENEMY_elf), closest_ENEMY_elf,
                                               game.ice_troll_max_speed) \
                                    >= turns_to_travel(game, closest_my_elf, closest_ENEMY_elf,
                                                       game.elf_max_speed) + game.ice_troll_summoning_duration - 2:
                                # -2 because we want our ice troll will tank if the enemy elf will fight back
                                if not is_targeted_by_my_icetroll(game, closest_ENEMY_elf):
                                    summon_with_closest_portal(game, ICE, closest_ENEMY_elf)
                            smart_movement(game, closest_my_elf, enemy_portal.location)

                    elif closest_ENEMY_elf.distance(my_castle) < first_arrow_portal.distance(my_castle):
                        if does_win_fight(game, closest_my_elf, closest_ENEMY_elf):
                            attack_object(game, closest_my_elf, closest_ENEMY_elf)
                            print "elf %s is attacking : %s" % (closest_my_elf, closest_ENEMY_elf)

                        else:
                            smart_movement(game, closest_my_elf, closest_ENEMY_elf.get_location())
                            print "elf %s is moving to : %s" % (closest_my_elf, closest_ENEMY_elf.get_location()

            else:
                # no enemy portals
                for enemy_elf in game.get_enemy_living_elves():
                    if enemy_elf.distance(my_castle) < first_arrow_portal.distance(my_castle):
                        closest_my_elf = get_closest_my_elf(game, enemy_elf)
                        if does_win_fight(game, closest_my_elf, enemy_elf):
                                attack_object(game, closest_my_elf, enemy_elf)
                        else:
                            smart_movement(game, closest_my_elf, enemy_elf)
                            if turns_to_travel(game, get_closest_my_portal(game, enemy_elf), enemy_elf,
                                               game.ice_troll_max_speed) \
                                    >= turns_to_travel(game, closest_my_elf, enemy_elf,
                                                       game.elf_max_speed) + game.ice_troll_summoning_duration - 2:
                                # -2 because we want our ice troll will tank if the enemy elf will fight back
                                if not is_targeted_by_my_icetroll(game, enemy_elf):
                                    summon_with_closest_portal(game, ICE, enemy_elf)

        else:
            # no enemy elves
            for enemy_portal in game.get_enemy_portals():
                if enemy_portal.distance(my_castle) < first_arrow_portal.distance(my_castle):
                    closest_my_elf = get_closest_my_elf(game, enemy_portal)
                    if does_win_fight(game, closest_my_elf, enemy_portal):
                        attack_object(game, closest_my_elf, enemy_portal)
                    else:
                        smart_movement(game, closest_my_elf, enemy_portal)
                        if turns_to_travel(game, get_closest_my_portal(game, enemy_portal), enemy_portal,
                                           game.ice_troll_max_speed) \
                                >= turns_to_travel(game, closest_my_elf, enemy_elf,
                                                   game.elf_max_speed) + game.ice_troll_summoning_duration - 2:
                            # -2 because we want our ice troll will tank if the enemy elf will fight back
                            if not is_targeted_by_my_icetroll(game, enemy_portal):
                                summon_with_closest_portal(game, ICE, enemy_portal)

                '''
                if enemy_elf.is_building() and first_arrow_portal.distance(enemy_elf) > enemy_elf.distance(my_castle):
                    if game.get_my_living_elves():
                        closest_my_elf = get_closest_my_elf(game, enemy_elf).attack_object(enemy_elf)
                        if does_win_fight(game, closest_my_elf, enemy_elf):
                            attack_object(game, closest_my_elf, enemy_elf)
                        if turns_to_travel(game, get_closest_my_portal(game, enemy_elf), enemy_elf, game.ice_troll_max_speed)\
                                >= turns_to_travel(game, closest_my_elf, enemy_elf, game.elf_max_speed) + 3:
                            get_closest_my_portal(game, enemy_elf).summon_ice_troll()
                '''


def get_next_arrow_portal_loc(game):
    """

    This function get the next location for a portal in the arrow attack

    :param game:
    :return: the location of the next location for a portal in the arrow attack
    :type: Location
    """
    if Globals.arrow_next_portal_loc and game.get_my_portals() == Globals.prev_game.get_my_portals():
        return Globals.arrow_next_portal_loc
    else:
        portals = get_objects_in_path(game, game.get_my_castle(), game.get_enemy_castle(), game.get_my_portals()) + \
                  [game.get_my_castle().get_location().towards(game.get_enemy_castle(), 10)]
        for elf in game.get_my_living_elves():
            if elf.is_building:
                portals.append(elf.get_location())
        first_portal = closest(game, game.get_enemy_castle(), portals)
        print "first_portal:", first_portal
        Globals.arrow_next_portal_loc = first_portal.get_location().towards(game.get_enemy_castle(),
                                                                            game.castle_size + game.portal_size)
        return Globals.arrow_next_portal_loc
