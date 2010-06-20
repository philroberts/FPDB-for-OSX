#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
#        0  Do not use a name like "xyz_2". Names ending in _ and a single digit are
#           used to indicate the number of decimal places the user wants to see in the Hud.
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
#           The stat_dict keys should be in lower case, i.e. vpip not VPIP, since
#           postgres returns the column names in lower case.
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
#import sys

#    pyGTK modules
import pygtk
import gtk
import re

#    FreePokerTools modules
import Configuration
import Database
import Charset


re_Places = re.compile("_[0-9]$")
re_Percent = re.compile("%$")

# String manipulation
import codecs
encoder = codecs.lookup(Configuration.LOCALE_ENCODING)

def do_tip(widget, tip):
    _tip = Charset.to_utf8(tip)
    widget.set_tooltip_text(_tip)

def do_stat(stat_dict, player = 24, stat = 'vpip'):
    match = re_Places.search(stat)
    if match is None:
        result = eval("%(stat)s(stat_dict, %(player)d)" % {'stat': stat, 'player': player})
    else:
        base = stat[0:-2]
        places = int(stat[-1:])
        result = eval("%(stat)s(stat_dict, %(player)d)" % {'stat': base, 'player': player})
        match = re_Percent.search(result[1])
        if match is None:
            result = (result[0], "%.*f" % (places, result[0]), result[2], result[3], result[4], result[5])
        else:
            result = (result[0], "%.*f%%" % (places, 100*result[0]), result[2], result[3], result[4], result[5])
    return result

#    OK, for reference the tuple returned by the stat is:
#    0 - The stat, raw, no formating, eg 0.33333333
#    1 - formatted stat with appropriate precision and punctuation, eg 33%
#    2 - formatted stat with appropriate precision, punctuation and a hint, eg v=33%
#    3 - same as #2 except name of stat instead of hint, eg vpip=33%
#    4 - the calculation that got the stat, eg 9/27
#    5 - the name of the stat, useful for a tooltip, eg vpip

########################################### 
#    functions that return individual stats

def totalprofit(stat_dict, player):
    """    Total Profit."""
    if stat_dict[player]['net'] != 0:
        stat = float(stat_dict[player]['net']) / 100
        return (stat, '$%.2f' % stat, 'tp=$%.2f' % stat, 'totalprofit=$%.2f' % stat, str(stat), 'Total Profit')
    return ('0', '$0.00', 'tp=0', 'totalprofit=0', '0', 'Total Profit')

def playername(stat_dict, player):
    """    Player Name."""
    return (stat_dict[player]['screen_name'],
            stat_dict[player]['screen_name'],
            stat_dict[player]['screen_name'],
            stat_dict[player]['screen_name'],
            stat_dict[player]['screen_name'],
            stat_dict[player]['screen_name'])

def vpip(stat_dict, player):
    """    Voluntarily put $ in the pot pre-flop."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['vpip'])/float(stat_dict[player]['n'])
        return (stat,
                '%3.1f'      % (100*stat) + '%',
                'v=%3.1f'    % (100*stat) + '%',
                'vpip=%3.1f' % (100*stat) + '%',
                '(%d/%d)'    % (stat_dict[player]['vpip'], stat_dict[player]['n']),
                'Voluntarily Put In Pot Pre-Flop%'
                )
    except: return (stat,
                    '%3.1f'      % (0) + '%',
                    'v=%3.1f'    % (0) + '%',
                    'vpip=%3.1f' % (0) + '%',
                    '(%d/%d)'    % (0, 0),
                    'Voluntarily Put In Pot Pre-Flop%'
                    )

def pfr(stat_dict, player):
    """    Preflop (3rd street) raise."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['pfr'])/float(stat_dict[player]['n'])
        return (stat,
                '%3.1f'      % (100*stat) + '%',
                'p=%3.1f'    % (100*stat) + '%',
                'pfr=%3.1f'  % (100*stat) + '%',
                '(%d/%d)'    % (stat_dict[player]['pfr'], stat_dict[player]['n']),
                'Pre-Flop Raise %'
                )
    except: 
        return (stat,
                '%3.1f'      % (0) + '%',
                'p=%3.1f'    % (0) + '%',
                'pfr=%3.1f' % (0) + '%',
                '(%d/%d)'    % (0, 0),
                'Pre-Flop Raise %'
                )

def wtsd(stat_dict, player):
    """    Went to SD when saw flop/4th."""
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
    """    Won $ at showdown."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['wmsd'])/float(stat_dict[player]['sd'])
        return (stat,
                '%3.1f'      % (100*stat) + '%',
                'w=%3.1f'    % (100*stat) + '%',
                'wmsd=%3.1f' % (100*stat) + '%',
                '(%5.1f/%d)'    % (float(stat_dict[player]['wmsd']), stat_dict[player]['sd']),
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

def profit100(stat_dict, player):
    """    Profit won per 100 hands (no decimal places)."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['net'])/float(stat_dict[player]['n'])
        return (stat,
                '%.0f'        % (100.0*stat),
                'p=%.0f'     % (100.0*stat),
                'p/100=%.0f'  % (100.0*stat),
                '%d/%d' % (stat_dict[player]['net'], stat_dict[player]['n']),
                'profit/100hands'
                )
    except:
            print "exception calcing p/100: 100 * %d / %d" % (stat_dict[player]['net'], stat_dict[player]['n'])
            return (stat,
                    '%.0f'       % (0),
                    'p=%.0f'     % (0),
                    'p/100=%.0f'  % (0),
                    '(%d/%d)' % (0, 0),
                    'profit/100hands'
                    )

def saw_f(stat_dict, player):
    """    Saw flop/4th."""
    try:
        num = float(stat_dict[player]['saw_f'])
        den = float(stat_dict[player]['n'])
        stat = num/den
        return (stat,
            '%3.1f'      % (100*stat) + '%',
            'sf=%3.1f'    % (100*stat) + '%',
            'saw_f=%3.1f' % (100*stat) + '%',
            '(%d/%d)'    % (stat_dict[player]['saw_f'], stat_dict[player]['n']),
            'Flop Seen %'
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
            'Flop Seen %'
            )

def n(stat_dict, player):
    """    Number of hands played."""
    try:
        # If sample is large enough, use X.Yk notation instead
        _n = stat_dict[player]['n']
        fmt = '%d' % _n
        if _n >= 10000:
            k = _n / 1000
            c = _n % 1000
            _c = float(c) / 100.0
            d = int(round(_c))
            if d == 10:
                k += 1
                d = 0
            fmt = '%d.%dk' % (k, d)
        return (stat_dict[player]['n'],
                '%s'        % fmt,
                'n=%d'      % (stat_dict[player]['n']),
                'n=%d'      % (stat_dict[player]['n']),
                '(%d)'      % (stat_dict[player]['n']),
                'number hands seen'
                )
    except:
        return (0,
                '%d'        % (0),
                'n=%d'      % (0),
                'n=%d'      % (0),
                '(%d)'      % (0),
                'number hands seen'
                )
    
def fold_f(stat_dict, player):
    """    Folded flop/4th."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['fold_2'])/float(stat_dict[player]['saw_f'])
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
    """    Steal %."""
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
        return (stat, 'NA', 'st=NA', 'steal=NA', '(0/0)', '% steal attempted')

def f_SB_steal(stat_dict, player):
    """    Folded SB to steal."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['sbnotdef'])/float(stat_dict[player]['sbstolen'])
        return (stat,
                '%3.1f'        % (100*stat) + '%',
                'fSB=%3.1f'     % (100*stat) + '%',
                'fSB_s=%3.1f' % (100*stat) + '%',
                '(%d/%d)'      % (stat_dict[player]['sbnotdef'], stat_dict[player]['sbstolen']),
                '% folded SB to steal'
                )
    except:
        return (stat,
                'NA',
                'fSB=NA',
                'fSB_s=NA',
                '(0/0)',
                '% folded SB to steal')

def f_BB_steal(stat_dict, player):
    """    Folded BB to steal."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['bbnotdef'])/float(stat_dict[player]['bbstolen'])
        return (stat,
                '%3.1f'        % (100*stat) + '%',
                'fBB=%3.1f'     % (100*stat) + '%',
                'fBB_s=%3.1f' % (100*stat) + '%',
                '(%d/%d)'      % (stat_dict[player]['bbnotdef'], stat_dict[player]['bbstolen']),
                '% folded BB to steal'
                )
    except:
        return (stat,
                'NA',
                'fBB=NA',
                'fBB_s=NA',
                '(0/0)',
                '% folded BB to steal')

def three_B(stat_dict, player):
    """    Three bet preflop/3rd."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['tb_0'])/float(stat_dict[player]['tb_opp_0'])
        return (stat,
                '%3.1f'        % (100*stat) + '%',
                '3B=%3.1f'     % (100*stat) + '%',
                '3B_pf=%3.1f'  % (100*stat) + '%',
                '(%d/%d)'      % (stat_dict[player]['tb_0'], stat_dict[player]['tb_opp_0']),
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
    """    Won $ when saw flop/4th."""
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

def a_freq1(stat_dict, player):
    """    Flop/4th aggression frequency."""
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
    
def a_freq2(stat_dict, player):
    """    Turn/5th aggression frequency."""
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
    
def a_freq3(stat_dict, player):
    """    River/6th aggression frequency."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_3'])/float(stat_dict[player]['saw_3'])
        return (stat,
                '%3.1f'        % (100*stat) + '%',
                'a3=%3.1f'     % (100*stat) + '%',
                'a_fq_3=%3.1f'  % (100*stat) + '%',
                '(%d/%d)'      % (stat_dict[player]['aggr_3'], stat_dict[player]['saw_3']),
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
    
def a_freq4(stat_dict, player):
    """    7th street aggression frequency."""
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
                'a4=%3.1f'     % (0) + '%',
                'a_fq_4=%3.1f' % (0) + '%',
                '(%d/%d)'      % (0, 0),
                'Aggression Freq 7th'
                )

def a_freq_123(stat_dict, player):
    """    Post-Flop aggression frequency."""
    stat = 0.0
    try:
        stat = float(  stat_dict[player]['aggr_1'] + stat_dict[player]['aggr_2'] + stat_dict[player]['aggr_3']
                    ) / float(  stat_dict[player]['saw_1'] + stat_dict[player]['saw_2'] + stat_dict[player]['saw_3']);
        return (stat,
                '%3.1f'             % (100*stat) + '%',
                'afq=%3.1f'         % (100*stat) + '%',
                'postf_aggfq=%3.1f' % (100*stat) + '%',
                '(%d/%d)'           % (  stat_dict[player]['aggr_1']
                                       + stat_dict[player]['aggr_2']
                                       + stat_dict[player]['aggr_3']
                                      ,  stat_dict[player]['saw_1']
                                       + stat_dict[player]['saw_2']
                                       + stat_dict[player]['saw_3']
                                      ),
                'Post-Flop Aggression Freq'
                )
    except:
        return (stat,
                '%2.0f'        % (0) + '%',
                'a3=%2.0f'     % (0) + '%',
                'a_fq_3=%2.0f' % (0) + '%',
                '(%d/%d)'      % (0, 0),
                'Post-Flop Aggression Freq'
                )
    
def cb1(stat_dict, player):
    """    Flop continuation bet."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['cb_1'])/float(stat_dict[player]['cb_opp_1'])
        return (stat,
                '%3.1f'        % (100*stat) + '%',
                'cb1=%3.1f'     % (100*stat) + '%',
                'cb_1=%3.1f'  % (100*stat) + '%',
                '(%d/%d)'      % (stat_dict[player]['cb_1'], stat_dict[player]['cb_opp_1']),
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
    
def cb2(stat_dict, player):
    """    Turn continuation bet."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['cb_2'])/float(stat_dict[player]['cb_opp_2'])
        return (stat,
                '%3.1f'        % (100*stat) + '%',
                'cb2=%3.1f'     % (100*stat) + '%',
                'cb_2=%3.1f'  % (100*stat) + '%',
                '(%d/%d)'      % (stat_dict[player]['cb_2'], stat_dict[player]['cb_opp_2']),
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
    
def cb3(stat_dict, player):
    """    River continuation bet."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['cb_3'])/float(stat_dict[player]['cb_opp_3'])
        return (stat,
                '%3.1f'        % (100*stat) + '%',
                'cb3=%3.1f'     % (100*stat) + '%',
                'cb_3=%3.1f'  % (100*stat) + '%',
                '(%d/%d)'      % (stat_dict[player]['cb_3'], stat_dict[player]['cb_opp_3']),
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
    
def cb4(stat_dict, player):
    """    7th street continuation bet."""
    stat = 0.0
    try:
        stat = float(stat_dict[player]['cb_4'])/float(stat_dict[player]['cb_opp_4'])
        return (stat,
                '%3.1f'        % (100*stat) + '%',
                'cb4=%3.1f'     % (100*stat) + '%',
                'cb_4=%3.1f'  % (100*stat) + '%',
                '(%d/%d)'      % (stat_dict[player]['cb_4'], stat_dict[player]['cb_opp_4']),
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
    
def ffreq1(stat_dict, player):
    """    Flop/4th fold frequency."""
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
    
def ffreq2(stat_dict, player):
    """    Turn/5th fold frequency."""
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
    
def ffreq3(stat_dict, player):
    """    River/6th fold frequency."""
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
    
def ffreq4(stat_dict, player):
    """    7th fold frequency."""
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
    db_connection = Database.Database(c)
    h = db_connection.get_last_hand()
    stat_dict = db_connection.get_stats_from_hand(h, "ring")
    
    for player in stat_dict.keys():
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'vpip') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'pfr') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'wtsd') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'profit100') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'saw_f') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'n') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'fold_f') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'wmsd') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'steal') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'f_SB_steal') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'f_BB_steal') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'three_B')
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'WMsF') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'a_freq1') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'a_freq2') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'a_freq3') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'a_freq4') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'a_freq_123') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'cb1') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'cb2') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'cb3') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'cb4') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'ffreq1') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'ffreq2') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'ffreq3') 
        print "player = ", player, do_stat(stat_dict, player = player, stat = 'ffreq4')
        print "\n" 

    print "\n\nLegal stats:"
    print "(add _0 to name to display with 0 decimal places, _1 to display with 1, etc)\n"
    for attr in dir():
        if attr.startswith('__'): continue
        if attr in ("Configuration", "Database", "GInitiallyUnowned", "gtk", "pygtk",
                    "player", "c", "db_connection", "do_stat", "do_tip", "stat_dict",
                    "h", "re", "re_Percent", "re_Places"): continue
        print "%-14s %s" % (attr, eval("%s.__doc__" % (attr)))
#        print "            <pu_stat pu_stat_name = \"%s\"> </pu_stat>" % (attr)
    print

    db_connection.close_connection

