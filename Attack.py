"""
############
Attack
############
.. module:: Attack

"""

from trainingBot import *
import Globals


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
        attacking_portal_destination, safe_range = best_attacking_portal_location(game, attack_dest)
        turn_limit_for_dest = turns_to_travel(game, elf.get_location(), attacking_portal_destination, elf.max_speed,
                                              smart=True)
    else:
        attacking_portal_destination, safe_range = kwargs["attacking_portal_destination"]
        turn_limit_for_dest = kwargs["turn_limit_for_dest"]

    if turns_to_travel(game, elf.get_location(), attacking_portal_destination, elf.max_speed,
                       smart=True) > turn_limit_for_dest + offset:
        handle_obstacle(game, elf, attacking_portal_destination)
    elif not elf.get_location().in_range(attacking_portal_destination, safe_range) or not elf.can_build_portal():
        if game.get_my_mana() < game.portal_cost:
            mana_state = "save mana"
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


def handle_obstacle(game, elf, attacking_portal_destination):
    """



    :param game:
    :type game: Game
    :param elf:
    :type elf: Elf
    :param attacking_portal_destination:
    :type attacking_portal_destination: Location
    :return:
    """
    pass  # should identafy obstacles and call a function to handle this spesific obsticale.
    '''
    new_attacking_portal_destination, new_safe_range = pick_attacking_portal_destinaion(game, attack_dest)
    new_turn_limit_for_dest = turns_to_travel(game, elf.get_location(), new_attacking_portal_destination, elf.max_speed, smart=True)
    if elf.get_location().distance(new_attacking_portal_destination) < elf.get_location().distance(new_attacking_portal_destination):
        attacking_portal_destination, safe_range = new_attacking_portal_destination, new_safe_range
        turn_limit_for_dest = new_turn_limit_for_dest
    else:
    '''


def best_attacking_portal_location(game, attack_dest):
    """

    :param game:
    :param attack_dest:
    :return:
    :type: (x, y)
    """
    pass  # eyal's
