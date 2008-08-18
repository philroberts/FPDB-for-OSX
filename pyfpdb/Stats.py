#!/usr/bin/env python

"""Manage collecting and formatting of stats and tooltips.
"""
#    Copyright 2008, Ray E. Barker

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
#    Standard Library modules

#    pyGTK modules
import pygtk
import gtk

#    FreePokerTools modules
import Configuration
import Database

def do_tip(widget, tip):
    widget.set_tooltip_text(tip)

def do_stat(stat_dict, player = 24, stat = 'vpip'):
    return eval("%(stat)s(stat_dict, %(player)d)" % {'stat': stat, 'player': player})
#    OK, for reference the tuple returned by the stat is:
#    0 - The stat, raw, no formating, eg 0.33333333
#    1 - formatted stat with appropriate precision and punctuation, eg 33%
#    2 - formatted stat with appropriate precision, punctuation and a hint, eg v=33%
#    3 - same as #2 except name of stat instead of hint, eg vpip=33%
#    4 - the calculation that got the stat, eg 9/27
#    5 - the name of the stat, useful for a tooltip, eg vpip

########################################### 
#    functions that return individual stats
def vpip(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['vpip'])/float(stat_dict[player]['n'])
        return (stat, 
                '%3.1f'      % (100*stat) + '%', 
                'v=%3.1f'    % (100*stat) + '%', 
                'vpip=%3.1f' % (100*stat) + '%', 
                '(%d/%d)'    % (stat_dict[player]['vpip'], stat_dict[player]['n']),
                'vpip'
                )
    except: return (stat, 
                    '%3.1f'      % (0) + '%', 
                    'w=%3.1f'    % (0) + '%', 
                    'wtsd=%3.1f' % (0) + '%', 
                    '(%d/%d)'    % (0, 0),
                    'wtsd'
                    )

def pfr(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['pfr'])/float(stat_dict[player]['n'])
        return (stat, 
                '%3.1f'      % (100*stat) + '%', 
                'p=%3.1f'    % (100*stat) + '%', 
                'pfr=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'    % (stat_dict[player]['pfr'], stat_dict[player]['n']),
                'pfr'
                )
    except: 
        return (stat, 
                '%3.1f'      % (0) + '%', 
                'w=%3.1f'    % (0) + '%', 
                'wtsd=%3.1f' % (0) + '%', 
                '(%d/%d)'    % (0, 0),
                'wtsd'
                )

def wtsd(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['sd'])/float(stat_dict[player]['saw_f'])
        return (stat, 
                '%3.1f'      % (100*stat) + '%', 
                'w=%3.1f'    % (100*stat) + '%', 
                'wtsd=%3.1f' % (100*stat) + '%', 
                '(%d/%d)'    % (stat_dict[player]['sd'], stat_dict[player]['saw_f']),
                'wtsd'
                )
    except:
        return (stat, 
                '%3.1f'      % (0) + '%', 
                'w=%3.1f'    % (0) + '%', 
                'wtsd=%3.1f' % (0) + '%', 
                '(%d/%d)'    % (0, 0),
                'wtsd'
                )

    
def saw_f(stat_dict, player):
    try:
        num = float(stat_dict[player]['saw_f'])
        den = float(stat_dict[player]['n'])
        stat = num/den
        return (stat, 
            '%3.1f'      % (100*stat) + '%', 
            'sf=%3.1f'    % (100*stat) + '%', 
            'saw_f=%3.1f' % (100*stat) + '%', 
            '(%d/%d)'    % (stat_dict[player]['saw_f'], stat_dict[player]['n']),
            'saw_f'
            )
    except:
        stat = 0.0
        num = 0
        den = 0
        return (stat, 
            '%3.1f'       % (stat) + '%', 
            'sf=%3.1f'    % (stat) + '%', 
            'saw_f=%3.1f' % (stat) + '%', 
            '(%d/%d)'     % (num, den),
            'saw_f'
            )

def n(stat_dict, player):
    try:
        return (stat_dict[player]['n'], 
                '%d'        % (stat_dict[player]['n']), 
                'n=%d'      % (stat_dict[player]['n']), 
                'n=%d'      % (stat_dict[player]['n']), 
                '(%d)'      % (stat_dict[player]['n']),
                'number hands seen'
                )
    except:
        return (stat_dict[player][0], 
                '%d'        % (stat_dict[player][0]), 
                'n=%d'      % (stat_dict[player][0]), 
                'n=%d'      % (stat_dict[player][0]), 
                '(%d)'      % (stat_dict[player][0]),
                'number hands seen'
                )
    
def fold_f(stat_dict, player):
    stat = 0.0
    try:
        stat = stat_dict[player]['fold_2']/stat_dict[player]['saw_f']
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'ff=%3.1f'     % (100*stat) + '%', 
                'fold_f=%3.1f' % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['fold_2'], stat_dict[player]['saw_f']),
                'folded fourth'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'ff=%3.1f'     % (0) + '%', 
                'fold_f=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                'folded fourth'
                )
           

if __name__=="__main__":
    c = Configuration.Config()
    db_connection = Database.Database(c, 'fpdb', 'holdem')
    h = db_connection.get_last_hand()
    stat_dict = db_connection.get_stats_from_hand(h, 0)
    
    for player in stat_dict.keys():
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'vpip') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'pfr') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'wtsd') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'saw_f') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'n') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'fold_f') 
        
    db_connection.close

