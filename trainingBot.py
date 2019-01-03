"""
############
trainingBot
############
.. module:: MyBot
   :platform: Unix, Windows
   :synopsis: A useful module indeed.

.. moduleauthor:: Andrew Carter <andrew@invalid.com>


"""

from elf_kingdom import *

game = 0


def is_targeted_by_icetroll(map_object):
    """

    :param map_object: the map object which to check if is targeted bt ice trolls
    :type map_object: MapObject
    :return: return a list of the ice trolls which target obj
    :type: [Creature]
    """