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

#    How to write a new stat:
#        1  You can see a listing of all the raw stats (e.g., from the HudCache table)
#           by running Database.py as a stand along program.  You need to combine 
#           those raw stats to get stats to present to the HUD.  If you need more 
#           information than is in the HudCache table, then you have to write SQL.
#        2  The raw stats seen when you run Database.py are available in the Stats.py
#           in the stat_dict dict.  For example the number of vpips would be
#           stat_dict[player]['vpip'].  So the % vpip is 
#           float(stat_dict[player]['vpip'])/float(stat_dict[player]['n']).  You can see how the 
#           keys of stat_dict relate to the column names in HudCache by inspecting
#           the proper section of the SQL.py module.
#        3  You have to write a small function for each stat you want to add.  See
#           the vpip() function for example.  This function has to be protected from
#           exceptions, using something like the try:/except: paragraphs in vpip.
#        4  The name of the function has to be the same as the of the stat used
#           in the config file.
#        5  The stat functions have a peculiar return value, which is outlined in
#           the do_stat function.  This format is useful for tool tips and maybe
#           other stuff.
#        6  For each stat you make add a line to the __main__ function to test it.

#    Standard Library modules

#    pyGTK modules
import pygtk
import gtk

#    FreePokerTools modules
import Configuration
import Database

def do_tip(widget, tip):
    widget.set_tooltip_text(tip)

def list_stats():
            for key in dir():
                print key

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
    """
    Voluntarily put $ in the pot
    """
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
                'p=%3.1f'    % (0) + '%', 
                'pfr=%3.1f' % (0) + '%', 
                '(%d/%d)'    % (0, 0),
                'pfr'
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
                '% went to showdown'
                )
    except:
        return (stat, 
                '%3.1f'      % (0) + '%', 
                'w=%3.1f'    % (0) + '%', 
                'wtsd=%3.1f' % (0) + '%', 
                '(%d/%d)'    % (0, 0),
                '% went to showdown'
                )

def wmsd(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['wmsd'])/float(stat_dict[player]['sd'])
        return (stat, 
                '%3.1f'      % (100*stat) + '%', 
                'w=%3.1f'    % (100*stat) + '%', 
                'wmsd=%3.1f' % (100*stat) + '%', 
                '(%d/%d)'    % (stat_dict[player]['wmsd'], stat_dict[player]['sd']),
                '% won money at showdown'
                )
    except:
        return (stat, 
                '%3.1f'      % (0) + '%', 
                'w=%3.1f'    % (0) + '%', 
                'wmsd=%3.1f' % (0) + '%', 
                '(%d/%d)'    % (0, 0),
                '% won money at showdown'
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
        stat = float(stat_dict[player]['fold_2'])/fold(stat_dict[player]['saw_f'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'ff=%3.1f'     % (100*stat) + '%', 
                'fold_f=%3.1f' % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['fold_2'], stat_dict[player]['saw_f']),
                'folded flop/4th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'ff=%3.1f'     % (0) + '%', 
                'fold_f=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                'folded flop/4th'
                )
           
def steal(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['steal'])/float(stat_dict[player]['steal_opp'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'st=%3.1f'     % (100*stat) + '%', 
                'steal=%3.1f' % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['steal'], stat_dict[player]['steal_opp']),
                '% steal attempted'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'st=%3.1f'     % (0) + '%', 
                'steal=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% steal attempted'
                )

def f_SB_steal(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['SBnotDef'])/float(stat_dict[player]['SBstolen'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'fSB=%3.1f'     % (100*stat) + '%', 
                'fSB_s=%3.1f' % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['SBnotDef'], stat_dict[player]['SBstolen']),
                '% folded SB to steal'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'fSB=%3.1f'     % (0) + '%', 
                'fSB_s=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% folded SB to steal'
                )

def f_BB_steal(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['BBnotDef'])/float(stat_dict[player]['BBstolen'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'fBB=%3.1f'     % (100*stat) + '%', 
                'fBB_s=%3.1f' % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['BBnotDef'], stat_dict[player]['BBstolen']),
                '% folded BB to steal'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'fBB=%3.1f'     % (0) + '%', 
                'fBB_s=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% folded BB to steal'
                )

def three_B_0(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['TB_0'])/float(stat_dict[player]['TB_opp_0'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                '3B=%3.1f'     % (100*stat) + '%', 
                '3B_pf=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['TB_0'], stat_dict[player]['TB_opp_0']),
                '% 3/4 Bet preflop/3rd'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                '3B=%3.1f'     % (0) + '%', 
                '3B_pf=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% 3/4 Bet preflop/3rd'
                )

def WMsF(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['w_w_s_1'])/float(stat_dict[player]['saw_1'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'wf=%3.1f'     % (100*stat) + '%', 
                'w_w_f=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['w_w_s_1'], stat_dict[player]['saw_f']),
                '% won$/saw flop/4th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'wf=%3.1f'     % (0) + '%', 
                'w_w_f=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% won$/saw flop/4th'
                )

def a_freq_1(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_1'])/float(stat_dict[player]['saw_f'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'a1=%3.1f'     % (100*stat) + '%', 
                'a_fq_1=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['aggr_1'], stat_dict[player]['saw_f']),
                'Aggression Freq flop/4th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'a1=%3.1f'     % (0) + '%', 
                'a_fq_1=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                'Aggression Freq flop/4th'
                )
    
def a_freq_2(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_2'])/float(stat_dict[player]['saw_2'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'a2=%3.1f'     % (100*stat) + '%', 
                'a_fq_2=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['aggr_2'], stat_dict[player]['saw_2']),
                'Aggression Freq turn/5th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'a2=%3.1f'     % (0) + '%', 
                'a_fq_2=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                'Aggression Freq turn/5th'
                )
    
def a_freq_3(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_3'])/float(stat_dict[player]['saw_3'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'a3=%3.1f'     % (100*stat) + '%', 
                'a_fq_3=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['aggr_1'], stat_dict[player]['saw_1']),
                'Aggression Freq river/6th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'a3=%3.1f'     % (0) + '%', 
                'a_fq_3=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                'Aggression Freq river/6th'
                )
    
def a_freq_4(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_4'])/float(stat_dict[player]['saw_4'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'a4=%3.1f'     % (100*stat) + '%', 
                'a_fq_4=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['aggr_4'], stat_dict[player]['saw_4']),
                'Aggression Freq 7th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'a1=%3.1f'     % (0) + '%', 
                'a_fq_1=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                'Aggression Freq flop/4th'
                )
    
def cb_1(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['CB_1'])/float(stat_dict[player]['CB_opp_1'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'cb1=%3.1f'     % (100*stat) + '%', 
                'cb_1=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['CB_1'], stat_dict[player]['CB_opp_1']),
                '% continuation bet flop/4th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'cb1=%3.1f'     % (0) + '%', 
                'cb_1=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% continuation bet flop/4th'
                )
    
def cb_2(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['CB_2'])/float(stat_dict[player]['CB_opp_2'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'cb2=%3.1f'     % (100*stat) + '%', 
                'cb_2=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['CB_2'], stat_dict[player]['CB_opp_2']),
                '% continuation bet turn/5th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'cb2=%3.1f'     % (0) + '%', 
                'cb_2=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% continuation bet turn/5th'
                )
    
def cb_3(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['CB_3'])/float(stat_dict[player]['CB_opp_3'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'cb3=%3.1f'     % (100*stat) + '%', 
                'cb_3=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['CB_3'], stat_dict[player]['CB_opp_3']),
                '% continuation bet river/6th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'cb3=%3.1f'     % (0) + '%', 
                'cb_3=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% continuation bet river/6th'
                )
    
def cb_4(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['CB_4'])/float(stat_dict[player]['CB_opp_4'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'cb4=%3.1f'     % (100*stat) + '%', 
                'cb_4=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['CB_4'], stat_dict[player]['CB_opp_4']),
                '% continuation bet 7th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'cb4=%3.1f'     % (0) + '%', 
                'cb_4=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% continuation bet 7th'
                )
    
def ffreq_1(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_freq_1'])/float(stat_dict[player]['was_raised_1'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'ff1=%3.1f'     % (100*stat) + '%', 
                'ff_1=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['f_freq_1'], stat_dict[player]['was_raised_1']),
                '% fold frequency flop/4th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'ff1=%3.1f'     % (0) + '%', 
                'ff_1=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% fold frequency flop/4th'
                )
    
def ffreq_2(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_freq_2'])/float(stat_dict[player]['was_raised_2'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'ff2=%3.1f'     % (100*stat) + '%', 
                'ff_2=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['f_freq_2'], stat_dict[player]['was_raised_2']),
                '% fold frequency turn/5th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'ff2=%3.1f'     % (0) + '%', 
                'ff_2=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% fold frequency turn/5th'
                )
    
def ffreq_3(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_freq_3'])/float(stat_dict[player]['was_raised_3'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'ff3=%3.1f'     % (100*stat) + '%', 
                'ff_3=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['f_freq_3'], stat_dict[player]['was_raised_3']),
                '% fold frequency river/6th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'ff3=%3.1f'     % (0) + '%', 
                'ff_3=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% fold frequency river/6th'
                )
    
def ffreq_4(stat_dict, player):
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_freq_4'])/float(stat_dict[player]['was_raised_4'])
        return (stat,
                '%3.1f'        % (100*stat) + '%', 
                'ff4=%3.1f'     % (100*stat) + '%', 
                'ff_4=%3.1f'  % (100*stat) + '%', 
                '(%d/%d)'      % (stat_dict[player]['f_freq_4'], stat_dict[player]['was_raised_4']),
                '% fold frequency 7th'
                )
    except:
        return (stat,
                '%3.1f'        % (0) + '%', 
                'ff4=%3.1f'     % (0) + '%', 
                'ff_4=%3.1f' % (0) + '%', 
                '(%d/%d)'      % (0, 0),
                '% fold frequency 7th'
                )
    
if __name__== "__main__":
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
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'wmsd') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'steal') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'f_SB_steal') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'f_BB_steal') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'three_B_0') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'WMsF') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'a_freq_1') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'a_freq_2') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'a_freq_3') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'a_freq_4') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'cb_1') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'cb_2') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'cb_3') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'cb_4') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'ffreq_1') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'ffreq_2') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'ffreq_3') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'ffreq_4') 

#    print "\n\nLegal stats:"
#    for attr in dir():
#        if attr.startswith('__'): continue
#        if attr == 'Configuration' or attr == 'Database': continue
#        if attr == 'GInitiallyUnowned': continue
#        print attr.__doc__
#
#    print vpip.__doc__
    db_connection.close

