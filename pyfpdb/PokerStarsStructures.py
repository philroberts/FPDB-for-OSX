#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2010-2013, Chaz Littlejohn
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

########################################################################

from datetime import datetime
import pytz

class PokerStarsStructures:
    
    def __init__(self):
        self.versions = [pytz.utc.localize(datetime.strptime(d, "%Y/%m/%d %H:%M:%S")) for d in ("2011/05/05 00:00:00","2011/05/20 00:00:00")]
        self.versions.append(datetime.utcnow().replace(tzinfo = pytz.utc))
        self.SnG_Structures = []
        self.SnG_Structures.append({(150, 25, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    #Not unique (300, 40, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (600, 50, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (1500, 100, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (2500, 200, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (3500, 300, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (5500, 500, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (10492, 908, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (21000, 1500, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (32500, 2000, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (52500, 3000, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (105000, 5000, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (210000, 9000, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (100, 20, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (300, 40, 9): 'Normal', #7-10 handed, under 45 entrants #Not unique
                                    (545, 55, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (1000, 100, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (2000, 200, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (3000, 300, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (5000, 500, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (10000, 900, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (20000, 1500, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (30000, 2000, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (50000, 3000, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (100000, 5000, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (200000, 9000, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (300, 25, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    #Not unique (600, 60, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    #Not unique (1200, 100, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    #Not unique (2300, 200, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (3600, 300, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (5500, 500, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (7200, 600, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (11000, 900, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (22000, 1500, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (53500, 3000, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (106000, 5000, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (100, 20, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (300, 40, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (600, 60, 6): 'Normal', #6-handed, Under 30 Entrants #Not unique
                                    (1200, 100, 6): 'Normal', #6-handed, Under 30 Entrants #Not unique
                                    (2300, 200, 6): 'Normal', #6-handed, Under 30 Entrants #Not unique
                                    (3500, 300, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (5060, 440, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (7000, 600, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (11200, 900, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (30500, 2000, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (600, 25, 2): 'Turbo', #Heads Up
                                    (1100, 50, 2): 'Turbo', #Heads Up
                                    (2200, 100, 2): 'Turbo', #Heads Up
                                    (3300, 150, 2): 'Turbo', #Heads Up
                                    (5500, 250, 2): 'Turbo', #Heads Up
                                    (11000, 500, 2): 'Turbo', #Heads Up
                                    (22000, 1000, 2): 'Turbo', #Heads Up
                                    (33000, 1500, 2): 'Turbo', #Heads Up
                                    (55000, 2000, 2): 'Turbo', #Heads Up
                                    (110000, 3000, 2): 'Turbo', #Heads Up
                                    (220000, 5000, 2): 'Turbo', #Heads Up
                                    (550000, 10000, 2): 'Turbo', #Heads Up
                                    (200, 20, 2): 'Normal', #Heads Up
                                    (500, 25, 2): 'Normal', #Heads Up
                                    (1000, 50, 2): 'Normal', #Heads Up
                                    (2000, 100, 2): 'Normal', #Heads Up
                                    (3000, 150, 2): 'Normal', #Heads Up
                                    (5000, 250, 2): 'Normal', #Heads Up
                                    (10000, 500, 2): 'Normal', #Heads Up
                                    (20000, 1000, 2): 'Normal', #Heads Up
                                    (30000, 1500, 2): 'Normal', #Heads Up
                                    (50000, 2000, 2): 'Normal', #Heads Up
                                    (100000, 3000, 2): 'Normal', #Heads Up
                                    (200000, 5000, 2): 'Normal', #Heads Up
                                    (500000, 10000, 2): 'Normal', #Heads Up
                                    (50, 5, 45): 'Turbo', #45 Entrants
                                    (100, 10, 45): 'Turbo', #45 Entrants
                                    (300, 25, 45): 'Turbo', #45 Entrants
                                    (600, 50, 45): 'Turbo', #45 Entrants
                                    (1100, 100, 45): 'Turbo', #45 Entrants
                                    (2500, 200, 45): 'Turbo', #45 Entrants
                                    (3500, 300, 45): 'Turbo', #45 Entrants
                                    (5500, 500, 45): 'Turbo', #45 Entrants
                                    (10500, 900, 45): 'Turbo', #45 Entrants
                                    (25, 0, 45): 'Normal', #45 Entrants
                                    (100, 20, 45): 'Normal', #45 Entrants
                                    (500, 50, 45): 'Normal', #45 Entrants
                                    (1000, 100, 45): 'Normal', #45 Entrants
                                    (2000, 200, 45): 'Normal', #45 Entrants
                                    (50, 5, 90): 'Turbo', #90 Entrants
                                    (100, 10, 90): 'Turbo', #90 Entrants
                                    (300, 25, 90): 'Turbo', #90 Entrants
                                    (600, 50, 90): 'Turbo', #90 Entrants
                                    (1100, 100, 90): 'Turbo', #90 Entrants
                                    (5500, 500, 90): 'Turbo', #90 Entrants
                                    (100, 8, 10): 'Turbo', #Fifty50
                                    (500, 24, 10): 'Turbo', #Fifty50
                                    (1000, 48, 10): 'Turbo', #Fifty50
                                    (2000, 96, 10): 'Turbo', #Fifty50
                                    (3000, 144, 10): 'Turbo', #Fifty50
                                    (5000, 240, 10): 'Turbo', #Fifty50
                                    (10000, 430, 10): 'Turbo', #Fifty50
                                    (100, 11, 10): 'Normal', #Fifty50
                                    (500, 30, 10): 'Normal', #Fifty50
                                    (1000, 60, 10): 'Normal', #Fifty50
                                    (2000, 120, 10): 'Normal', #Fifty50
                                    (3000, 180, 10): 'Normal', #Fifty50
                                    (5000, 300, 10): 'Normal', #Fifty50
                                    (10000, 540, 10): 'Normal', #Fifty50
                                    (25, 0, 90): 'Normal', #90 Entrants
                                    (200, 20, 90): 'Normal', #90 Entrants
                                    (500, 50, 90): 'Normal', #90 Entrants
                                    (800, 80, 90): 'Normal', #90 Entrants
                                    (200, 20, 180): 'Turbo', #180 Entrants
                                    (700, 70, 180): 'Turbo', #180 Entrants
                                    (1100, 100, 180): 'Turbo', #180 Entrants
                                    (3300, 300, 180): 'Turbo', #180 Entrants
                                    (400, 40, 180): 'Normal', #180 Entrants
                                    (1000, 100, 180): 'Normal', #180 Entrants
                                    (2000, 200, 180): 'Normal', #180 Entrants
                                    (125, 10, 27): 'Normal', #27 Player Knockout
                                    (125, 15, 90): 'Normal', #90 Player Knockout
                                    (625, 50, 90): 'Normal', #90 Player Knockout
                                    (1250, 100, 90): 'Normal', #90 Player Knockout
                                    (300, 30, 180): 'Normal', #180 Player Rebuy
                                    })
        self.SnG_Structures.append({
                                    (100, 8, 9, 9): 'Hyper', #7-10 handed, under 45 entrants
                                    (500, 23, 9, 9): 'Hyper', #7-10 handed, under 45 entrants
                                    (500, 21, 6, 6): 'Hyper', #6-handed, Under 45 Entrants
                                    (500, 11, 2, 2): 'Hyper', #Heads Up
                                    })
        self.SnG_Structures.append({(132, 18, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (316, 34, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (645, 55, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (1389, 111, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (2778, 222, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (5556, 444, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (9280, 720, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (18780, 1220, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (28300, 1700, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (47400, 2600, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (95700, 4300, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (192300, 7700, 9): 'Turbo', #7-10 handed, under 45 entrants
                                    (129, 21, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (311, 39, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (637, 63, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (1370, 130, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (2740, 260, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (5480, 520, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (9215, 785, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (18650, 1350, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (28100, 1900, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (47175, 2825, 9): 'Normal', #7-10 handed, under 45 entrants
                                    (132, 18, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (319, 31, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (648, 52, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (1392, 108, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (2784, 216, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (5568, 432, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (9325, 675, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (18820, 1180, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (28370, 1630, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (47500, 2500, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (96000, 4000, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (192800, 7200, 6): 'Turbo', #6-handed, Under 30 Entrants
                                    (129, 21, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (313, 37, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (639, 61, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (1379, 121, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (2758, 242, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (5516, 484, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (9260, 740, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (18690, 1310, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (28170, 1830, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (47275, 2725, 6): 'Normal', #6-handed, Under 30 Entrants
                                    (140, 10, 2): 'Turbo', #Heads Up
                                    (332, 18, 2): 'Turbo', #Heads Up
                                    (671, 29, 2): 'Turbo', #Heads Up
                                    (1439, 61, 2): 'Turbo', #Heads Up
                                    (2878, 122, 2): 'Turbo', #Heads Up
                                    (5767, 233, 2): 'Turbo', #Heads Up
                                    (9632, 368, 2): 'Turbo', #Heads Up
                                    (19385, 615, 2): 'Turbo', #Heads Up
                                    (29125, 875, 2): 'Turbo', #Heads Up
                                    (48760, 1240, 2): 'Turbo', #Heads Up
                                    (97920, 2080, 2): 'Turbo', #Heads Up
                                    (196250, 3750, 2): 'Turbo', #Heads Up
                                    (493700, 6300, 2): 'Turbo', #Heads Up
                                    (138, 12, 2): 'Normal', #Heads Up
                                    (329, 21, 2): 'Normal', #Heads Up
                                    (667, 33, 2): 'Normal', #Heads Up
                                    (1429, 71, 2): 'Normal', #Heads Up
                                    (2857, 143, 2): 'Normal', #Heads Up
                                    (5728, 272, 2): 'Normal', #Heads Up
                                    (9569, 431, 2): 'Normal', #Heads Up
                                    (19275, 725, 2): 'Normal', #Heads Up
                                    (28985, 1015, 2): 'Normal', #Heads Up
                                    (48540, 1460, 2): 'Normal', #Heads Up
                                    (97560, 2440, 2): 'Normal', #Heads Up
                                    (195600, 4400, 2): 'Normal', #Heads Up
                                    (492600, 7400, 2): 'Normal', #Heads Up
                                    (45, 5, 45): 'Turbo', #45 Entrants
                                    (136, 14, 45): 'Turbo', #45 Entrants
                                    (319, 31, 45): 'Turbo', #45 Entrants
                                    (918, 82, 45): 'Turbo', #45 Entrants
                                    (2765, 235, 45): 'Turbo', #45 Entrants
                                    (136, 14, 48): 'Turbo', #48 Entrants
                                    (136, 14, 36): 'Turbo', #36 Entrants
                                    (23, 2, 45): 'Normal', #45 Entrants
                                    (91, 9, 45): 'Normal', #45 Entrants
                                    (546, 54, 45): 'Normal', #45 Entrants
                                    (45, 5, 90): 'Turbo', #90 Entrants
                                    (91, 9, 90): 'Turbo', #90 Entrants
                                    (139, 11, 10): 'Turbo', #Fifty50
                                    (330, 20, 10): 'Turbo', #Fifty50
                                    (668, 32, 10): 'Turbo', #Fifty50
                                    (1431, 69, 10): 'Turbo', #Fifty50
                                    (2863, 137, 10): 'Turbo', #Fifty50
                                    (5725, 275, 10): 'Turbo', #Fifty50
                                    (9586, 414, 10): 'Turbo', #Fifty50
                                    (19305, 695, 10): 'Turbo', #Fifty50
                                    (29160, 840, 10): 'Turbo', #Fifty50
                                    (48720, 1280, 10): 'Turbo', #Fifty50
                                    (135, 15, 10): 'Normal', #Fifty50
                                    (326, 24, 10): 'Normal', #Fifty50
                                    (660, 40, 10): 'Normal', #Fifty50
                                    (1415, 85, 10): 'Normal', #Fifty50
                                    (2830, 170, 10): 'Normal', #Fifty50
                                    (5660, 340, 10): 'Normal', #Fifty50
                                    (9490, 510, 10): 'Normal', #Fifty50
                                    (19135, 865, 10): 'Normal', #Fifty50
                                    (23, 2, 90): 'Normal', #90 Entrants
                                    (228, 22, 90): 'Normal', #90 Entrants
                                    (228, 22, 180): 'Turbo', #180 Entrants
                                    (734, 66, 180): 'Turbo', #180 Entrants
                                    (1377, 123, 180): 'Turbo', #180 Entrants
                                    (3213, 287, 180): 'Turbo', #180 Entrants
                                    (410, 40, 180): 'Normal', #180 Entrants
                                    (1005, 95, 180): 'Normal', #180 Entrants
                                    (9, 1, 240): 'Normal', #240 Entrants
                                    (9, 1, 360): 'Turbo', #360 Entrants
                                    (45, 5, 360): 'Turbo', #360 Entrants
                                    (135, 15, 90): 'Normal', #90 Player Knockout
                                    (650, 50, 90): 'Normal', #90 Player Knockout
                                    (319, 31, 180): 'Normal', #180 Player Rebuy
                                    (139, 11, 9): 'Hyper', #7-10 handed, under 45 entrants
                                    (331, 19, 9): 'Hyper', #7-10 handed, under 45 entrants
                                    (670, 30, 9): 'Hyper', #7-10 handed, under 45 entrants
                                    (1439, 61, 9): 'Hyper', #7-10 handed, under 45 entrants
                                    (2877, 123, 9): 'Hyper', #7-10 handed, under 45 entrants
                                    (5754, 246, 9): 'Hyper', #7-10 handed, under 45 entrants
                                    (9632, 368, 9): 'Hyper', #7-10 handed, under 45 entrants
                                    (19318, 682, 9): 'Hyper', #7-10 handed, under 45 entrants
                                    (140, 10, 6): 'Hyper', #6-handed, Under 30 Entrants
                                    (332, 18, 6): 'Hyper', #6-handed, Under 30 Entrants
                                    (671, 29, 6): 'Hyper', #6-handed, Under 30 Entrants
                                    (1441, 59, 6): 'Hyper', #6-handed, Under 30 Entrants
                                    (2883, 117, 6): 'Hyper', #6-handed, Under 30 Entrants
                                    (5766, 234, 6): 'Hyper', #6-handed, Under 30 Entrants
                                    (9649, 351, 6): 'Hyper', #6-handed, Under 30 Entrants
                                    (19352, 648, 6): 'Hyper', #6-handed, Under 30 Entrants
                                    (29140, 860, 6): 'Hyper', #6-handed, Under 30 Entrants
                                    (48752, 1248, 6): 'Hyper', #6-handed, Under 30 Entrants
                                    (144, 6, 2): 'Hyper', #Heads Up
                                    (340, 10, 2): 'Hyper', #Heads Up
                                    (685, 15, 2): 'Hyper', #Heads Up
                                    (1469, 31, 2): 'Hyper', #Heads Up
                                    (2937, 63, 2): 'Hyper', #Heads Up
                                    (5874, 126, 2): 'Hyper', #Heads Up
                                    (9812, 188, 2): 'Hyper', #Heads Up
                                    (19666, 334, 2): 'Hyper', #Heads Up
                                    (29551, 449, 2): 'Hyper', #Heads Up
                                    (49335, 665, 2): 'Hyper', #Heads Up
                                    (98880, 1120, 2): 'Hyper', #Heads Up
                                    (91, 9, 180): 'Hyper', #180 Entrants
                                    (2, 0, 990): 'Hyper', #990 Entrants
                                    })

    def lookupSnG(self, key, startTime):
        for i in range(len(self.versions)):
            if startTime < self.versions[i]:
                struct = self.SnG_Structures[i].get(key)
                return struct
                                    
                                    
                                    