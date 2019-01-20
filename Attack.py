"""
############
Attack
############
.. module:: Attack

"""

from trainingBot import *
import Globals
from collections import *


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
        kwargs["turn_limit_for_dest"] = turns_to_travel(game, elf, kwargs["attacking_portal_destination"][0],
                                                        elf.max_speed, smart=True)

    attacking_portal_destination, safe_range = kwargs["attacking_portal_destination"]
    turn_limit_for_dest = kwargs["turn_limit_for_dest"]

    if turns_to_travel(game, elf, attacking_portal_destination, elf.max_speed,
                       smart=True) > turn_limit_for_dest + offset:
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
        lava_giant_damage = game.lava_giant_max_health - (game.lava_giant_suffocation_per_turn *
                                                          turns_to_travel(game, portal, game.lava_giant_max_speed))

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
                             turns_to_travel(game, portal, game.get_enemy_castle(), game.lava_giant_max_speed))

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


def does_win_fight(game, elf, attack_target, max_depth=5):
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

    # print "elf: %s, attack_target %s" % (elf, attack_target)

    # loop over the next turns until elf or attack_target will die
    while curr_attack_target.current_health and curr_elf.current_health  and max_depth:
        curr_swapped_game = copy.deepcopy(curr_game)
        curr_swapped_game._hx___me, curr_swapped_game._hx___enemies = curr_game.get_enemy(), [curr_game.get_myself()]
        # print "----------%s---------" % (5 - max_depth)
        
        # print "enemy_ice_trolls: %s" % curr_game.get_enemy_ice_trolls()
        # print ",".join(str((portal, portal.turns_to_summon)) for portal in curr_game.get_enemy_portals())
        
        elf_next_turn_hp = get_next_turn_health(curr_game, curr_elf, include_elves=True)
        attack_target_next_turn_hp = get_next_turn_health(curr_swapped_game, curr_attack_target, include_elves=True)
        # print "curr_elf hp: %s, elf_next_turn_hp %s" % (curr_elf.current_health, elf_next_turn_hp)
        # print "curr_attack_target hp: %s, curr_attack_target %s" % (curr_attack_target.current_health, attack_target_next_turn_hp)

        if not curr_elf.in_attack_range(attack_target):
            curr_elf.location = curr_elf.get_location().towards(attack_target, game.elf_max_speed)

        next_turn_my_ice_trolls, next_turn_enemy_ice_trolls = predict_next_turn_ice_trolls(curr_game)
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
        max_depth -= 1

    if curr_elf.current_health > curr_attack_target.current_health:  # if we will  won
        # print "will win"
        return True
    else:  # if we lost or draw
        # print "will lose"
        return False
