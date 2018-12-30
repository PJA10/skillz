from elf_kingdom import *

ICE = "ice"
LAVA = "lava"

def do_turn(game):

    if game.turn == 1:
        prev_turns_elf_locations = get_locations(game, game.get_enemy_living_elves())
    
    mana = game.default_mana_per_turn + game.get_my_mana() 
	
    #handle_elves(game)
    handle_portals(game)
    if game.turn < 50:
        game.get_my_living_elves()[0].move_to(Location(0,0))
    else:
        for elf in game.get_my_living_elves():
            a = call(game, elf, game.get_enemy_castle(), {
            "attack_closest_enemy": (0.8,attack_closest_enemy) ,
            "attack_closest_portal": (0.9,attack_closest_portal),
            "attack_closest_elf": (1,attack_closest_elf)
        })
            print a, elf
            a(game, elf, 10000)


def normalize(game, elf, destination, func):
    d = 0
    if func == attack_closest_enemy:
        try:
            d= 1/elf.distance(get_closest_enemy(game, elf))
        except:
            d= 0
    
    if func == attack_closest_portal:
        try:
            d= 1/elf.distance(get_closest_portal(game, elf))
        except:
            d= 0
    
    if func == attack_closest_elf:
        try:
            d= 1/elf.distance(closest(game,elf, game.get_enemy_living_elves()))
        except:
            d= 0
    print d
    return d

    

def call(game, elf, destination, sliders):
    normal = max(sliders.items(), key = lambda slider: slider[1][0] * normalize(game, elf, destination, slider[1][1]))
    return normal[1][1]

    
    

def get_locations(game, objs):
  	
    if objs is []:
        print "You gave me an empty array"
        print "objs", objs
        return False
  
    locs = []
    for obj in objs:
    	locs.append(obj.get_location())
    	return locs

def is_elf_attacking_portal():
    enemy_elfs = game.get_enemy_living_elves()
    enemy_locs = get_locations(game, enemy_elfs)


def enemy_in_object_range(game, map_object, rng):
    closest_enemy = get_closest_enemy(game, game.get_my_castle())
    if closest_enemy == None:
        return False
    return closest_enemy.get_location().distance(map_object.get_location()) < rng
		

def elf_movment(elf, loc):
    print loc, elf
    elf.move_to(loc)
    
def make_portal(game, loc, elf):
    
    # Assumes Mana!
    
    if elf == None:
        return None
    if elf.get_location() == loc:
        if elf.can_build_portal():
            elf.build_portal()
            return True
        else:
            game.debug("Elf "+str(elf)+" Can't build portal at "+str(loc))
            return False    
    else:
        print("Move elf")
        elf_movment(elf, loc)    
        return True


def summon(game, portal, summon_str):
    
    # Assumes Mana!
    if not portal.can_summon_lava_giant() and summon_str == "lava":
        return False
        
    if not portal.can_summon_ice_troll() and summon_str == "ice":
        return False
    
    # Convert from string to 
    summon_dic = {
                    "ice": portal.summon_ice_troll,
                    "lava": portal.summon_lava_giant
                 }
    summon_dic[summon_str]()
    return True

    
def closest(game, obj_array, other):
  
  	# Get closest object to other in obj_array 
  
    min_obj = None
    if obj_array is [] or obj_array == None:
        return None
        
    for index, location in enumerate(get_locations(game, obj_array)):
        if min_obj == None or min_obj.get_location().subtract(other.get_location()) > location.subtract(other.get_location):
            min_obj = obj_array[index]
	
	return min_obj
    
def handle_elves(game):
    if len(game.get_my_living_elves()) == 0:
        return
    elfs = game.get_my_living_elves()
    elf_def = closest(game, elfs, game.get_my_castle())
    elfs.remove(elf_def)
    elf_atk = None
    if len(elfs) != 0:
        elf_atk = elfs[0]


    max_distance= 1300
    
    ports = game.get_my_portals()
    if len(ports) ==0:
        port_def = None
        port_atk = None
    else:
        port_def = closest(game, ports, game.get_my_castle())
        ports.remove(port_def)
        port_atk = None
        if len(ports) != 0:
            port_atk = ports[0]
    
    
    
    if port_def == None or port_def.distance(game.get_my_castle()) > 2000:
        port_atk = port_def
        port_def = None
        if not make_portal(game, game.get_my_castle().get_location().towards(game.get_enemy_castle(), 1000), elf_def):
            if not attack_closest_portal(game, elf_def, max_distance):
                attack_closest_enemy(game, elf_def, max_distance)
    else:
        if not attack_closest_portal(game, elf_def, max_distance):
                attack_closest_enemy(game, elf_def, max_distance)
    
    if elf_atk != None:
        if port_atk == None:
            if not make_portal(game, game.get_enemy_castle().get_location().towards(game.get_my_castle(),1000), elf_atk):
                if not attack_closest_portal(game, elf_atk, max_distance):
                    attack_closest_enemy(game, elf_atk, max_distance)
        else:
            if not attack_closest_portal(game, elf_atk, max_distance):
                    attack_closest_enemy(game, elf_atk, max_distance)
    
def get_closest_enemy(game, map_object):
    enemys = game.get_enemy_creatures() + game.get_enemy_living_elves()
    if len(enemys)== 0:
        return None
    closest_enemy = enemys[0]
    for enemy in enemys:
        if  map_object.distance(enemy) < map_object.distance(closest_enemy):
            closest_enemy = enemy
        
    return closest_enemy

def attack_closest_enemy(game, elf, max_distance):
    target = get_closest_enemy(game, elf)
    if not target:
        return False
        
    if target.distance(elf) < max_distance:
        if elf.in_attack_range(target):
            elf.attack(target)
            return True
        else:
            elf_movment(elf, target)
            return True
    

def get_closest_portal(game, map_object):
    portals = game.get_enemy_portals()
    if len(portals)== 0:
        return None
    closest_portal = portals[0]
    for portal in portals:
        if  map_object.distance(portal) < map_object.distance(closest_portal):
            closest_portal = portal
        
    return closest_portal

def attack_closest_portal(game, elf, max_distance):
    target = get_closest_portal(game, elf)
    if not target:
        return False
    
    if target.distance(elf) < max_distance:
        if elf.in_attack_range(target):
            elf.attack(target)
            return True
        else:
            elf_movment(elf, target)
            return True

def attack_closest_elf(game, elf, max_distance):
    try:
        target = game.get_enemy_living_elves()[0]
    except:
        return False
    if not target:
        return False
        
    if target.distance(elf) < max_distance:
        if elf.in_attack_range(target):
            elf.attack(target)
            return True
        else:
            elf_movment(elf, target)
            return True
            

def handle_portals(game):
    ports = game.get_my_portals()
    if len(ports) == 0:
        return
    port_def = closest(game, ports, game.get_my_castle())
    print "port_def", port_def
    ports.remove(port_def)
    port_atk = None
    if len(ports) != 0:
        port_atk = ports[0]
        
    if port_def.distance(game.get_my_castle()) > 2000:
        port_atk = port_def
        port_def = None
    if port_def!= None:
        if enemy_in_object_range(game, game.get_my_castle(), 3000):
            print("in if in handle_portals")
            if (game.get_my_ice_trolls() is None or len(game.get_my_ice_trolls()) < 3) or game.get_my_mana() > 200:
                summon(game, port_def, ICE)
    if port_atk != None:
        summon(game, port_atk, LAVA)

