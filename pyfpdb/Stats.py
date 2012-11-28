#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Manage collecting and formatting of stats and tooltips."""
#    Copyright 2008-2011, Ray E. Barker

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

import L10n
_ = L10n.get_translation()

#    Standard Library modules
import sys
from decimal import Decimal   # needed by hand_instance in m_ratio

#    pyGTK modules
import pygtk
import gtk
import re

#    FreePokerTools modules
import Configuration
import Database
import Charset
import Card
import Hand

import logging
if __name__ == "__main__":
    Configuration.set_logfile("fpdb-log.txt")
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("db")


re_Places = re.compile("_[0-9]$")

# String manipulation
import codecs
encoder = codecs.lookup(Configuration.LOCALE_ENCODING)

stat_descriptions = {}

# Since tuples are immutable, we have to create a new one when
# overriding any decimal placements. Copy old ones and recreate the
# second value in tuple to specified format-
def __stat_override(decimals, stat_vals):
    s = '%.*f' % (decimals, 100.0*stat_vals[0])
    res = (stat_vals[0], s, stat_vals[2],
            stat_vals[3], stat_vals[4], stat_vals[5])
    return res


def do_tip(widget, tip):
    _tip = Charset.to_utf8(tip)
    widget.set_tooltip_text(_tip)


def do_stat(stat_dict, player = 24, stat = 'vpip', hand_instance = None):
    statname = stat
    match = re_Places.search(stat)
    if match:   # override if necessary
        statname = stat[0:-2]
    
    if stat in ['starthands','m_ratio','bbstack', 'game_abbr']:
        if hand_instance:
            result = eval("%(stat)s(stat_dict, %(player)d, hand_instance)" %
                {'stat': statname, 'player': player})
        else:
            return ((''),(''),(''),(''),(''),(''))
    else:
        result = eval("%(stat)s(stat_dict, %(player)d)" %
            {'stat': statname, 'player': player})

    # If decimal places have been defined, override result[1]
    # NOTE: decimal place override ALWAYS assumes the raw result is a
    # fraction (x/100); manual decimal places really only make sense for
    # percentage values. Also, profit/100 hands (bb/BB) already default
    # to three decimal places anyhow, so they are unlikely override
    # candidates.
    if match:
        places = int(stat[-1:])
        result = __stat_override(places, result)
    return result

#    OK, for reference the tuple returned by the stat is:
#    0 - The stat, raw, no formating, eg 0.33333333
#    1 - formatted stat with appropriate precision, eg. 33; shown in HUD
#    2 - formatted stat with appropriate precision, punctuation and a hint, eg v=33%
#    3 - same as #2 except name of stat instead of hint, eg vpip=33%
#    4 - the calculation that got the stat, eg 9/27
#    5 - the name of the stat, useful for a tooltip, eg vpip

########################################### 
#    functions that return individual stats


def totalprofit(stat_dict, player):
    stat_descriptions["totalprofit"] = _("Total Profit") + " (totalprofit)"
    if stat_dict[player]['net'] != 0:
        stat = float(stat_dict[player]['net']) / 100
        return (stat, '$%.2f' % stat, 'tp=$%.2f' % stat, 'totalprofit=$%.2f' % stat, str(stat), _('Total Profit'))
    return ('0', '$0.00', 'tp=0', 'totalprofit=0', '0', _('Total Profit'))

def playername(stat_dict, player):
    stat_descriptions["playername"] = _("Player Name") + " (playername)"
    return (stat_dict[player]['screen_name'],
            stat_dict[player]['screen_name'],
            stat_dict[player]['screen_name'],
            stat_dict[player]['screen_name'],
            stat_dict[player]['screen_name'],
            stat_dict[player]['screen_name'])

def calculate_end_stack(stat_dict, player, hand_instance):
    #fixme - move this code into Hands.py - it really belongs there

    #To reflect the end-of-hand position, we need a end-stack calculation
    # fixme, is there an easier way to do this from the hand_instance???
    # can't seem to find a hand_instance "end_of_hand_stack" attribute
    
    #First, find player stack size at the start of the hand
    
    stack = 0.0
    for item in hand_instance.players:
        if item[1] == stat_dict[player]['screen_name']:
            stack = float(item[2])
            
    #Next, deduct all action from this player
    for street in hand_instance.bets:
        for item in hand_instance.bets[street]:
            if item == stat_dict[player]['screen_name']:
                for amount in hand_instance.bets[street][stat_dict[player]['screen_name']]:
                    stack -= float(amount)
    
    #Next, add back any money returned
    for p in hand_instance.pot.returned:
        if p == stat_dict[player]['screen_name']:
            stack += float(hand_instance.pot.returned[p])
        
    #Finally, add back any winnings
    for item in hand_instance.collectees:
        if item == stat_dict[player]['screen_name']:
            stack += float(hand_instance.collectees[item])
    return stack

def m_ratio(stat_dict, player, hand_instance):
    
    #Tournament M-ratio calculation
    # Using the end-of-hand stack count vs. that hand's antes/blinds
         
    stat_descriptions["M ratio (last hand)"] = _("M") + " (M)"
    
    # sum all blinds/antes
    compulsory_bets = 0.0
    for p in hand_instance.bets['BLINDSANTES']:
        for i in hand_instance.bets['BLINDSANTES'][p]:
            compulsory_bets += float(i)
    compulsory_bets += float(hand_instance.gametype['sb'])
    compulsory_bets += float(hand_instance.gametype['bb'])
    
    stack = calculate_end_stack(stat_dict, player, hand_instance)

    if compulsory_bets != 0:
        stat = stack / compulsory_bets
    else:
        stat = 0

    return      ((int(stat)),
                '%d'        % (int(stat)),
                'M=%d'      % (int(stat)),
                'M=%d'      % (int(stat)),
                '(%d)'      % (int(stat)),
                _('M ratio') )

def bbstack(stat_dict, player, hand_instance):
    #Tournament Stack calculation in Big Blinds
    #Result is end of hand stack count / Current Big Blind limit
    stat_descriptions["Stack in bb"] = _("bb") + " (bb)"
    # current big blind limit
    current_bigblindlimit = 0
    current_bigblindlimit += float(hand_instance.gametype['bb'])
    
    stack = calculate_end_stack(stat_dict, player, hand_instance)

    if current_bigblindlimit != 0:
        stat = stack / current_bigblindlimit
    else:
        stat = 0

    return      ((int(stat)),
                '%d'        % (int(stat)),
                "bb's=%d"      % (int(stat)),
                "#bb's=%d"      % (int(stat)),
                '(%d)'      % (int(stat)),
                _('bb stack') )

def playershort(stat_dict, player):
    stat_descriptions["playershort"] = (_("Player Name")+" 1-5") + " (playershort)"
    r = stat_dict[player]['screen_name']
    if (len(r) > 6):
        r = r[:5] + "."
    return (r,
            r,
            r,
            r,
            stat_dict[player]['screen_name'],
            (_("Player Name")+" 1-5")
            )
            
def vpip(stat_dict, player):
    stat_descriptions["vpip"] = _("Voluntarily put in preflop/3rd street %") + " (vpip)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['vpip'])/float(stat_dict[player]['n'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'v=%3.1f%%'     % (100.0*stat),
                'vpip=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['vpip'], stat_dict[player]['n']),
                _('Voluntarily put in preflop/3rd street %')
                )
    except: return (stat,
                    'NA',
                    'v=NA',
                    'vpip=NA',
                    '(0/0)',
                    _('Voluntarily put in preflop/3rd street %')
                    )

def pfr(stat_dict, player):
    stat_descriptions["pfr"] = _("Preflop/3rd street raise %") + " (pfr)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['pfr'])/float(stat_dict[player]['n'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'p=%3.1f%%'     % (100.0*stat),
                'pfr=%3.1f%%'   % (100.0*stat),
                '(%d/%d)'    % (stat_dict[player]['pfr'], stat_dict[player]['n']),
                _('Preflop/3rd street raise %')
                )
    except: 
        return (stat,
                'NA',
                'p=NA',
                'pfr=NA',
                '(0/0)',
                _('Preflop/3rd street raise %')
                )

def wtsd(stat_dict, player):
    stat_descriptions["wtsd"] = _("% went to showdown when seen flop/4th street") + " (wtsd)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['sd'])/float(stat_dict[player]['saw_f'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'w=%3.1f%%'     % (100.0*stat),
                'wtsd=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['sd'], stat_dict[player]['saw_f']),
                _('% went to showdown when seen flop/4th street')
                )
    except:
        return (stat,
                'NA',
                'w=NA',
                'wtsd=NA',
                '(0/0)',
                _('% went to showdown when seen flop/4th street')
                )

def wmsd(stat_dict, player):
    stat_descriptions["wmsd"] = _("% won some money at showdown") + " (wmsd)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['wmsd'])/float(stat_dict[player]['sd'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'w=%3.1f%%'     % (100.0*stat),
                'wmsd=%3.1f%%'  % (100.0*stat),
                '(%5.1f/%d)'    % (float(stat_dict[player]['wmsd']), stat_dict[player]['sd']),
                _('% won some money at showdown')
                )
    except:
        return (stat,
                'NA',
                'w=NA',
                'wmsd=NA',
                '(0/0)',
                _('% won some money at showdown')
                )

# Money is stored as pennies, so there is an implicit 100-multiplier
# already in place
def profit100(stat_dict, player):
    stat_descriptions["profit100"] = _("Profit per 100 hands") + " (profit100)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['net'])/float(stat_dict[player]['n'])
        return (stat,
                '%.2f'          % (stat),
                'p=%.2f'        % (stat),
                'p/100=%.2f'    % (stat),
                '%d/%d' % (stat_dict[player]['net'], stat_dict[player]['n']),
                _('Profit per 100 hands')
                )
    except:
        log.info(_("exception calculating %s") % ("p/100: 100 * %d / %d" % (stat_dict[player]['net'], stat_dict[player]['n'])))
        return (stat,
                    'NA',
                    'p=NA',
                    'p/100=NA',
                    '(0/0)',
                    _('Profit per 100 hands')
                    )

def bbper100(stat_dict, player):
    stat_descriptions["bbper100"] = _("Big blinds won per 100 hands") + " (bbper100)"
    stat = 0.0
    #['bigblind'] is already containing number of hands * table's bigblind (e.g. 401 hands @ 5c BB = 2005)
    try:
        stat = 100.0 * float(stat_dict[player]['net']) / float(stat_dict[player]['bigblind'])
        return (stat,
                '%5.3f'         % (stat),
                'bb100=%5.3f'   % (stat),
                'bb100=%5.3f'   % (stat),
                '(%d,%d)'       % (100*stat_dict[player]['net'],stat_dict[player]['bigblind']),
                _('Big blinds won per 100 hands')
                )
    except:
        log.info(_("exception calculating %s") % ("bb/100: "+str(stat_dict[player])))
        return (stat,
                'NA',
                'bb100=NA',
                'bb100=NA',
                '(--)',
                _('Big blinds won per 100 hands')
                )

def BBper100(stat_dict, player):
    stat_descriptions["BBper100"] = _("Big bets won per 100 hands") + " (BBper100)"
    stat = 0.0
    #['bigblind'] is already containing number of hands * table's bigblind (e.g. 401 hands @ 5c BB = 2005)
    try:
        stat = 50 * float(stat_dict[player]['net']) / float(stat_dict[player]['bigblind'])
        return (stat,
                '%5.3f'         % (stat),
                'BB100=%5.3f'   % (stat),
                'BB100=%5.3f'   % (stat),
                '(%d,%d)'       % (100*stat_dict[player]['net'],2*stat_dict[player]['bigblind']),
                _('Big bets won per 100 hands')
                )
    except:
        log.info(_("exception calculating %s") % ("BB/100: "+str(stat_dict[player])))
        return (stat,
                'NA',
                'BB100=NA',
                'BB100=NA',
                '(--)',
                _('Big bets won per 100 hands')
                )

def saw_f(stat_dict, player):
    stat_descriptions["saw_f"] = _("Flop/4th street seen %") + " (saw_f)"
    try:
        num = float(stat_dict[player]['saw_f'])
        den = float(stat_dict[player]['n'])
        stat = num/den
        return (stat,
            '%3.1f'         % (100.0*stat),
            'sf=%3.1f%%'    % (100.0*stat),
            'saw_f=%3.1f%%' % (100.0*stat),
            '(%d/%d)'       % (stat_dict[player]['saw_f'], stat_dict[player]['n']),
            _('Flop/4th street seen %')
            )
    except:
        stat = 0.0
        return (stat,
            'NA',
            'sf=NA',
            'saw_f=NA',
            '(0/0)',
            _('Flop/4th street seen %')
            )

def n(stat_dict, player):
    stat_descriptions["n"] = _("Number of hands seen") + " (n)"
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
                _('Number of hands seen')
                )
    except:
        # Number of hands shouldn't ever be "NA"; zeroes are better here
        return (0,
                '%d'        % (0),
                'n=%d'      % (0),
                'n=%d'      % (0),
                '(%d)'      % (0),
                _('Number of hands seen')
                )
    
def fold_f(stat_dict, player):
    #TODO: remove
    stat = 0.0
    try:
        stat = float(stat_dict[player]['fold_2'])/float(stat_dict[player]['saw_f'])
        return (stat,
                '%3.1f'             % (100.0*stat),
                'ff=%3.1f%%'        % (100.0*stat),
                'fold_f=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'           % (stat_dict[player]['fold_2'], stat_dict[player]['saw_f']),
                ('folded flop/4th')
                )
    except:
        return (stat,
                'NA',
                'ff=NA',
                'fold_f=NA',
                '(0/0)',
                ('folded flop/4th')
                )
           
def steal(stat_dict, player):
    stat_descriptions["steal"] = _("% steal attempted") + " (steal)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['steal'])/float(stat_dict[player]['steal_opp'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'st=%3.1f%%'    % (100.0*stat),
                'steal=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['steal'], stat_dict[player]['steal_opp']),
                _('% steal attempted')
                )
    except:
        return (stat, 'NA', 'st=NA', 'steal=NA', '(0/0)', '% steal attempted')

def s_steal(stat_dict, player):
    stat_descriptions["s_steal"] = _("% steal success") + " (s_steal)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['suc_st'])/float(stat_dict[player]['steal'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                's_st=%3.1f%%'    % (100.0*stat),
                's_steal=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['suc_st'], stat_dict[player]['steal']),
                _('% steal success')
                )
    except:
        return (stat, 'NA', 'st=NA', 's_steal=NA', '(0/0)', '% steal success')

def f_SB_steal(stat_dict, player):
    stat_descriptions["f_SB_steal"] = _("% folded SB to steal") + " (f_SB_steal)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['sbnotdef'])/float(stat_dict[player]['sbstolen'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'fSB=%3.1f%%'   % (100.0*stat),
                'fSB_s=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['sbnotdef'], stat_dict[player]['sbstolen']),
                _('% folded SB to steal'))
    except:
        return (stat,
                'NA',
                'fSB=NA',
                'fSB_s=NA',
                '(0/0)',
                _('% folded SB to steal'))

def f_BB_steal(stat_dict, player):
    stat_descriptions["f_BB_steal"] = _("% folded BB to steal") + " (f_BB_steal)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['bbnotdef'])/float(stat_dict[player]['bbstolen'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'fBB=%3.1f%%'   % (100.0*stat),
                'fBB_s=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['bbnotdef'], stat_dict[player]['bbstolen']),
                _('% folded BB to steal'))
    except:
        return (stat,
                'NA',
                'fBB=NA',
                'fBB_s=NA',
                '(0/0)',
                _('% folded BB to steal'))
                
def f_steal(stat_dict, player):
    stat_descriptions["f_steal"] = _("% folded blind to steal") + " (f_steal)"
    stat = 0.0
    try:
        folded_blind = stat_dict[player]['sbnotdef'] + stat_dict[player]['bbnotdef']
        blind_stolen = stat_dict[player]['sbstolen'] + stat_dict[player]['bbstolen']
        
        stat = float(folded_blind)/float(blind_stolen)
        return (stat,
                '%3.1f'         % (100.0*stat),
                'fB=%3.1f%%'    % (100.0*stat),
                'fB_s=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (folded_blind, blind_stolen),
                _('% folded blind to steal'))
    except:
        return (stat,
                'NA',
                'fB=NA',
                'fB_s=NA',
                '(0/0)',
                _('% folded blind to steal'))

def three_B(stat_dict, player):
    stat_descriptions["three_B"] = _("% 3 bet preflop/3rd street") + " (three_B)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['tb_0'])/float(stat_dict[player]['tb_opp_0'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                '3B=%3.1f%%'    % (100.0*stat),
                '3B_pf=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['tb_0'], stat_dict[player]['tb_opp_0']),
                _('% 3 bet preflop/3rd street'))
    except:
        return (stat,
                'NA',
                '3B=NA',
                '3B_pf=NA',
                '(0/0)',
                _('% 3 bet preflop/3rd street'))

def four_B(stat_dict, player):
    stat_descriptions["four_B"] = _("% 4 bet preflop/3rd street") + " (four_B)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['fb_0'])/float(stat_dict[player]['fb_opp_0'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                '4B=%3.1f%%'    % (100.0*stat),
                '4B=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['fb_0'], stat_dict[player]['fb_opp_0']),
                _('% 4 bet preflop/3rd street'))
    except:
        return (stat,
                'NA',
                '4B=NA',
                '4B=NA',
                '(0/0)',
                _('% 4 bet preflop/3rd street'))

def cfour_B(stat_dict, player):
    stat_descriptions["cfour_B"] = _("% cold 4 bet preflop/3rd street") + " (cfour_B)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['cfb_0'])/float(stat_dict[player]['cfb_opp_0'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'C4B=%3.1f%%'    % (100.0*stat),
                'C4B_pf=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['cfb_0'], stat_dict[player]['cfb_opp_0']),
                _('% cold 4 bet preflop/3rd street'))
    except:
        return (stat,
                'NA',
                'C4B=NA',
                'C4B_pf=NA',
                '(0/0)',
                _('% cold 4 bet preflop/3rd street'))

# Four Bet Range
def fbr(stat_dict, player):
    stat_descriptions["fbr"] = _("4 bet range") + " (fbr)"
    stat = 0.0
    try: 
        stat = float(stat_dict[player]['fb_0'])/float(stat_dict[player]['fb_opp_0'])
        stat *= float(stat_dict[player]['pfr'])/float(stat_dict[player]['n'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'fbr=%3.1f%%'    % (100.0*stat),
                'fbr=%3.1f%%' % (100.0*stat),
                '(pfr*four_B)',
                _('4 bet range'))
    except:
        return (stat,
                'NA',
                'fbr=NA',
                'fbr=NA',
                '(pfr*four_B)',
                _('4 bet range'))

# Call 3 Bet
def ctb(stat_dict, player):
    stat_descriptions["ctb"] = _("% call 3 bet") + " (ctb)"
    stat = 0.0
    try: 
        stat = (float(stat_dict[player]['f3b_opp_0'])-float(stat_dict[player]['f3b_0'])-float(stat_dict[player]['fb_0']))/float(stat_dict[player]['f3b_opp_0'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'ctb=%3.1f%%'    % (100.0*stat),
                'ctb=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (float(stat_dict[player]['f3b_opp_0'])-stat_dict[player]['fb_0']-stat_dict[player]['f3b_0'], stat_dict[player]['fb_opp_0']),
                _('% call 3 bet'))
    except:
        return (stat,
                'NA',
                'ctb=NA',
                'ctb=NA',
                '(0/0)',
                _('% call 3 bet'))

def dbr1(stat_dict, player):
    stat_descriptions["dbr1"] = _("% DonkBetAndRaise flop/4th street") + " (dbr1)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_1']) - float(stat_dict[player]['cb_1'])
        stat /= float(stat_dict[player]['saw_f']) - float(stat_dict[player]['cb_opp_1'])
        return (stat,
                '%3.1f'             % (100.0*stat),
                'dbr1=%3.1f%%'        % (100.0*stat),
                'dbr1=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'      % (float(stat_dict[player]['aggr_1']) - float(stat_dict[player]['cb_1']), float(stat_dict[player]['saw_f']) - float(stat_dict[player]['cb_opp_1'])),
                _('% DonkBetAndRaise flop/4th street'))
    except:
        return (stat,
                'NA',
                'dbr1=NA',
                'dbr1=NA',
                '(0/0)',
                _('% DonkBetAndRaise flop/4th street'))

def dbr2(stat_dict, player):
    stat_descriptions["dbr2"] = _("% DonkBetAndRaise turn/5th street") + " (dbr2)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_2']) - float(stat_dict[player]['cb_2'])
        stat /= float(stat_dict[player]['saw_2']) - float(stat_dict[player]['cb_opp_2'])
        return (stat,
                '%3.1f'             % (100.0*stat),
                'dbr2=%3.1f%%'        % (100.0*stat),
                'dbr2=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'      % (float(stat_dict[player]['aggr_2']) - float(stat_dict[player]['cb_2']), float(stat_dict[player]['saw_2']) - float(stat_dict[player]['cb_opp_2'])),
                _('% DonkBetAndRaise turn/5th street'))
    except:
        return (stat,
                'NA',
                'dbr2=NA',
                'dbr2=NA',
                '(0/0)',
                _('% DonkBetAndRaise turn/5th street'))

def dbr3(stat_dict, player):
    stat_descriptions["dbr3"] = _("% DonkBetAndRaise river/6th street") + " (dbr3)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_3']) - float(stat_dict[player]['cb_3'])
        stat /= float(stat_dict[player]['saw_3']) - float(stat_dict[player]['cb_opp_3'])
        return (stat,
                '%3.1f'             % (100.0*stat),
                'dbr3=%3.1f%%'        % (100.0*stat),
                'dbr3=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'      % (float(stat_dict[player]['aggr_3']) - float(stat_dict[player]['cb_3']), float(stat_dict[player]['saw_3']) - float(stat_dict[player]['cb_opp_3'])),
                _('% DonkBetAndRaise river/6th street'))
    except:
        return (stat,
                'NA',
                'dbr3=NA',
                'dbr3=NA',
                '(0/0)',
                _('% DonkBetAndRaise river/6th street'))


def f_dbr1(stat_dict, player):
    stat_descriptions["f_dbr1"] = _("% Fold to DonkBetAndRaise flop/4th street") + " (f_dbr1)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_freq_1']) - float(stat_dict[player]['f_cb_1'])
        stat /= float(stat_dict[player]['was_raised_1']) - float(stat_dict[player]['f_cb_opp_1'])
        return (stat,
                '%3.1f'             % (100.0*stat),
                'f_dbr1=%3.1f%%'        % (100.0*stat),
                'f_dbr1=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'      % (float(stat_dict[player]['f_freq_1']) - float(stat_dict[player]['f_cb_1']), float(stat_dict[player]['was_raised_1']) - float(stat_dict[player]['f_cb_opp_1'])),
                _('% Fold to DonkBetAndRaise flop/4th street'))
    except:
        return (stat,
                'NA',
                'f_dbr1=NA',
                'f_dbr1=NA',
                '(0/0)',
                _('% Fold DonkBetAndRaise flop/4th street'))

def f_dbr2(stat_dict, player):
    stat_descriptions["f_dbr2"] = _("% Fold to DonkBetAndRaise turn") + " (f_dbr2)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_freq_2']) - float(stat_dict[player]['f_cb_2'])
        stat /= float(stat_dict[player]['was_raised_2']) - float(stat_dict[player]['f_cb_opp_2'])
        return (stat,
                '%3.1f'             % (100.0*stat),
                'f_dbr2=%3.1f%%'        % (100.0*stat),
                'f_dbr2=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'      % (float(stat_dict[player]['f_freq_2']) - float(stat_dict[player]['f_cb_2']), float(stat_dict[player]['was_raised_2']) - float(stat_dict[player]['f_cb_opp_2'])),
                _('% Fold to DonkBetAndRaise turn'))
    except:
        return (stat,
                'NA',
                'f_dbr2=NA',
                'f_dbr2=NA',
                '(0/0)',
                _('% Fold DonkBetAndRaise turn'))


def f_dbr3(stat_dict, player):
    stat_descriptions["f_dbr3"] = _("% Fold to DonkBetAndRaise river") + " (f_dbr3)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_freq_3']) - float(stat_dict[player]['f_cb_3'])
        stat /= float(stat_dict[player]['was_raised_3']) - float(stat_dict[player]['f_cb_opp_3'])
        return (stat,
                '%3.1f'             % (100.0*stat),
                'f_dbr3=%3.1f%%'        % (100.0*stat),
                'f_dbr3=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'      % (float(stat_dict[player]['f_freq_3']) - float(stat_dict[player]['f_cb_3']), float(stat_dict[player]['was_raised_3']) - float(stat_dict[player]['f_cb_opp_3'])),
                _('% Fold to DonkBetAndRaise river'))
    except:
        return (stat,
                'NA',
                'f_dbr3=NA',
                'f_dbr3=NA',
                '(0/0)',
                _('% Fold DonkBetAndRaise river'))


def squeeze(stat_dict, player):
    stat_descriptions["squeeze"] = _("% squeeze preflop") + " (squeeze)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['sqz_0'])/float(stat_dict[player]['sqz_opp_0'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'SQZ=%3.1f%%'    % (100.0*stat),
                'SQZ_pf=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['sqz_0'], stat_dict[player]['sqz_opp_0']),
                _('% squeeze preflop'))
    except:
        return (stat,
                'NA',
                'SQZ=NA',
                'SQZ_pf=NA',
                '(0/0)',
                _('% squeeze preflop'))


def raiseToSteal(stat_dict, player):
    stat_descriptions["raiseToSteal"] = _("% raise to steal") + " (raiseToSteal)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['rts'])/float(stat_dict[player]['rts_opp'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'RST=%3.1f%%'    % (100.0*stat),
                'RST_pf=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['rts'], stat_dict[player]['rts_opp']),
                _('% raise to steal'))
    except:
        return (stat,
                'NA',
                'RST=NA',
                'RST_pf=NA',
                '(0/0)',
                _('% raise to steal'))

def car0(stat_dict, player):
    stat_descriptions["car0"] = _("% called a raise preflop") + " (car0)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['car0'])/float(stat_dict[player]['car_opp_0'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'CAR0=%3.1f%%'    % (100.0*stat),
                'CAR_pf=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['car0'], stat_dict[player]['car_opp_0']),
                _('% called a raise preflop'))
    except:
        return (stat,
                'NA',
                'CAR0=NA',
                'CAR_pf=NA',
                '(0/0)',
                _('% called a raise preflop'))

def f_3bet(stat_dict, player):
    stat_descriptions["f_3bet"] = _("% fold to 3 bet preflop/3rd street") + " (f_3bet)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f3b_0'])/float(stat_dict[player]['f3b_opp_0'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'F3B=%3.1f%%'    % (100.0*stat),
                'F3B_pf=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['f3b_0'], stat_dict[player]['f3b_opp_0']),
                _('% fold to 3 bet preflop/3rd street'))
    except:
        return (stat,
                'NA',
                'F3B=NA',
                'F3B_pf=NA',
                '(0/0)',
                _('% fold to 3 bet preflop/3rd street'))

def f_4bet(stat_dict, player):
    stat_descriptions["f_4bet"] = _("% fold to 4 bet preflop/3rd street") + " (f_4bet)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f4b_0'])/float(stat_dict[player]['f4b_opp_0'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'F4B=%3.1f%%'    % (100.0*stat),
                'F4B_pf=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['f4b_0'], stat_dict[player]['f4b_opp_0']),
                _('% fold to 4 bet preflop/3rd street'))
    except:
        return (stat,
                'NA',
                'F4B=NA',
                'F4B_pf=NA',
                '(0/0)',
                _('% fold to 4 bet preflop/3rd street'))

def WMsF(stat_dict, player):
    stat_descriptions["WMsF"] = _("% won money when seen flop/4th street") + " (WMsF)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['w_w_s_1'])/float(stat_dict[player]['saw_1'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'wf=%3.1f%%'    % (100.0*stat),
                'w_w_f=%3.1f%%' % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['w_w_s_1'], stat_dict[player]['saw_f']),
                _('% won money when seen flop/4th street'))
    except:
        return (stat,
                'NA',
                'wf=NA',
                'w_w_f=NA',
                '(0/0)',
                _('% won money when seen flop/4th street'))

def a_freq1(stat_dict, player):
    stat_descriptions["a_freq1"] = _("Aggression frequency flop/4th street") + " (a_freq1)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_1'])/float(stat_dict[player]['saw_f'])
        return (stat,
                '%3.1f'             % (100.0*stat),
                'a1=%3.1f%%'        % (100.0*stat),
                'a_fq_1=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'      % (stat_dict[player]['aggr_1'], stat_dict[player]['saw_f']),
                _('Aggression frequency flop/4th street'))
    except:
        return (stat,
                'NA',
                'a1=NA',
                'a_fq_1=NA',
                '(0/0)',
                _('Aggression frequency flop/4th street'))
    
def a_freq2(stat_dict, player):
    stat_descriptions["a_freq2"] = _("Aggression frequency turn/5th street") + " (a_freq2)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_2'])/float(stat_dict[player]['saw_2'])
        return (stat,
                '%3.1f'             % (100.0*stat),
                'a2=%3.1f%%'        % (100.0*stat),
                'a_fq_2=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'           % (stat_dict[player]['aggr_2'], stat_dict[player]['saw_2']),
                _('Aggression frequency turn/5th street'))
    except:
        return (stat,
                'NA',
                'a2=NA',
                'a_fq_2=NA',
                '(0/0)',
                _('Aggression frequency turn/5th street'))
    
def a_freq3(stat_dict, player):
    stat_descriptions["a_freq3"] = _("Aggression frequency river/6th street") + " (a_freq3)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_3'])/float(stat_dict[player]['saw_3'])
        return (stat,
                '%3.1f'             % (100.0*stat),
                'a3=%3.1f%%'        % (100.0*stat),
                'a_fq_3=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'      % (stat_dict[player]['aggr_3'], stat_dict[player]['saw_3']),
                _('Aggression frequency river/6th street'))
    except:
        return (stat,
                'NA',
                'a3=NA',
                'a_fq_3=NA',
                '(0/0)',
                _('Aggression frequency river/6th street'))
    
def a_freq4(stat_dict, player):
    stat_descriptions["a_freq4"] = _("Aggression frequency 7th street") + " (a_freq4)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['aggr_4'])/float(stat_dict[player]['saw_4'])
        return (stat,
                '%3.1f'             % (100.0*stat),
                'a4=%3.1f%%'        % (100.0*stat),
                'a_fq_4=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'           % (stat_dict[player]['aggr_4'], stat_dict[player]['saw_4']),
                _('Aggression frequency 7th street'))
    except:
        return (stat,
                'NA',
                'a4=NA',
                'a_fq_4=NA',
                '(0/0)',
                _('Aggression frequency 7th street'))

def a_freq_123(stat_dict, player):
    stat_descriptions["a_freq_123"] = _("Post-flop aggression frequency") + " (a_freq_123)"
    stat = 0.0
    try:
        stat = float(  stat_dict[player]['aggr_1'] + stat_dict[player]['aggr_2'] + stat_dict[player]['aggr_3']
                    ) / float(  stat_dict[player]['saw_1'] + stat_dict[player]['saw_2'] + stat_dict[player]['saw_3']);
        return (stat,
                '%3.1f'                 % (100.0*stat),
                'afq=%3.1f%%'           % (100.0*stat),
                'postf_aggfq=%3.1f%%'   % (100.0*stat),
                '(%d/%d)'           % (  stat_dict[player]['aggr_1']
                                       + stat_dict[player]['aggr_2']
                                       + stat_dict[player]['aggr_3']
                                      ,  stat_dict[player]['saw_1']
                                       + stat_dict[player]['saw_2']
                                       + stat_dict[player]['saw_3']
                                      ),
                _('Post-flop aggression frequency'))
    except:
        return (stat,
                'NA',
                'a3=NA',
                'a_fq_3=NA',
                '(0/0)',
                _('Post-flop aggression frequency'))

def agg_freq(stat_dict, player):
    #TODO: remove, dupe of a_freq_123
    stat = 0.0
    try:
        #Agression on the flop and all streets
        bet_raise = stat_dict[player]['aggr_1'] + stat_dict[player]['aggr_2'] + stat_dict[player]['aggr_3'] + stat_dict[player]['aggr_4']
        #number post flop streets seen, this must be number of post-flop calls !!
        post_call  = stat_dict[player]['call_1'] + stat_dict[player]['call_2'] + stat_dict[player]['call_3'] + stat_dict[player]['call_4']
        #Number of post flop folds this info is not yet in the database
        post_fold = stat_dict[player]['f_freq_1'] + stat_dict[player]['f_freq_2'] + stat_dict[player]['f_freq_3'] + stat_dict[player]['f_freq_4']

        stat = float (bet_raise) / float(post_call + post_fold + bet_raise)

        return (stat,
                '%3.1f'             % (100.0*stat),
                'afr=%3.1f%%'       % (100.0*stat),
                'agg_fr=%3.1f%%'    % (100.0*stat),
                '(%d/%d)'           % (bet_raise, (post_call + post_fold + bet_raise)),
                ('Aggression Freq'))
    except:
        return (stat,
                'NA',
                'af=NA',
                'agg_f=NA',
                '(0/0)',
                ('Aggression Freq'))

def agg_fact(stat_dict, player):
    stat_descriptions["agg_fact"] = _("Aggression factor") + " (agg_fact)"
    stat = 0.0
    try:
        bet_raise =   stat_dict[player]['aggr_1'] + stat_dict[player]['aggr_2'] + stat_dict[player]['aggr_3'] + stat_dict[player]['aggr_4']
        post_call  =  stat_dict[player]['call_1'] + stat_dict[player]['call_2'] + stat_dict[player]['call_3'] + stat_dict[player]['call_4']
       
        if post_call > 0:
            stat = float (bet_raise) / float(post_call)
        else:
            stat = float (bet_raise)
        return (stat,
                '%2.2f'        % (stat) ,
                'afa=%2.2f'    % (stat) ,
                'agg_fa=%2.2f' % (stat) ,
                '(%d/%d)'      % (bet_raise, post_call),
                _('Aggression factor'))
    except:
        return (stat,
                'NA',
                'afa=NA',
                'agg_fa=NA',
                '(0/0)',
                _('Aggression factor'))
        
def agg_fact_pct(stat_dict, player):
    stat_descriptions["agg_fact_pct"] = _("Aggression factor pct") + " (agg_fact_pct)"
    stat = 0.0
    try:
        bet_raise =   stat_dict[player]['aggr_1'] + stat_dict[player]['aggr_2'] + stat_dict[player]['aggr_3'] + stat_dict[player]['aggr_4']
        post_call  =  stat_dict[player]['call_1'] + stat_dict[player]['call_2'] + stat_dict[player]['call_3'] + stat_dict[player]['call_4']
       
        stat = float (bet_raise) / float(post_call + bet_raise)
        return (stat,
                '%2.2f'        % (stat) ,
                'afap=%2.2f'    % (stat) ,
                'agg_fa_pct=%2.2f' % (stat) ,
                '(%d/%d)'      % (bet_raise, post_call),
                _('Aggression factor pct'))
    except:
        return (stat,
                'NA',
                'afap=NA',
                'agg_fa_pct=NA',
                '(0/0)',
                _('Aggression factor pct'))

def cbet(stat_dict, player):
    stat_descriptions["cbet"] = _("% continuation bet") + " (cbet)"
    stat = 0.0
    try:
        cbets = stat_dict[player]['cb_1']+stat_dict[player]['cb_2']+stat_dict[player]['cb_3']+stat_dict[player]['cb_4']
        oppt = stat_dict[player]['cb_opp_1']+stat_dict[player]['cb_opp_2']+stat_dict[player]['cb_opp_3']+stat_dict[player]['cb_opp_4']
        stat = float(cbets)/float(oppt)
        return (stat,
                '%3.1f'         % (100.0*stat),
                'cbet=%3.1f%%'  % (100.0*stat),
                'cbet=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (cbets, oppt),
                _('% continuation bet'))
    except:
        return (stat,
                'NA',
                'cbet=NA',
                'cbet=NA',
                '(0/0)',
                _('% continuation bet'))
    
def cb1(stat_dict, player):
    stat_descriptions["cb1"] = _("% continuation bet flop/4th street") + " (cb1)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['cb_1'])/float(stat_dict[player]['cb_opp_1'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'cb1=%3.1f%%'   % (100.0*stat),
                'cb_1=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['cb_1'], stat_dict[player]['cb_opp_1']),
                _('% continuation bet flop/4th street'))
    except:
        return (stat,
                'NA',
                'cb1=NA',
                'cb_1=NA',
                '(0/0)',
                _('% continuation bet flop/4th street'))
    
def cb2(stat_dict, player):
    stat_descriptions["cb2"] = _("% continuation bet turn/5th street") + " (cb2)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['cb_2'])/float(stat_dict[player]['cb_opp_2'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'cb2=%3.1f%%'   % (100.0*stat),
                'cb_2=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['cb_2'], stat_dict[player]['cb_opp_2']),
                _('% continuation bet turn/5th street'))
    except:
        return (stat,
                'NA',
                'cb2=NA',
                'cb_2=NA',
                '(0/0)',
                _('% continuation bet turn/5th street'))
    
def cb3(stat_dict, player):
    stat_descriptions["cb3"] = _("% continuation bet river/6th street") + " (cb3)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['cb_3'])/float(stat_dict[player]['cb_opp_3'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'cb3=%3.1f%%'   % (100.0*stat),
                'cb_3=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['cb_3'], stat_dict[player]['cb_opp_3']),
                _('% continuation bet river/6th street'))
    except:
        return (stat,
                'NA',
                'cb3=NA',
                'cb_3=NA',
                '(0/0)',
                _('% continuation bet river/6th street'))
    
def cb4(stat_dict, player):
    stat_descriptions["cb4"] = _("% continuation bet 7th street") + " (cb4)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['cb_4'])/float(stat_dict[player]['cb_opp_4'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'cb4=%3.1f%%'   % (100.0*stat),
                'cb_4=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'      % (stat_dict[player]['cb_4'], stat_dict[player]['cb_opp_4']),
                _('% continuation bet 7th street'))
    except:
        return (stat,
                'NA',
                'cb4=NA',
                'cb_4=NA',
                '(0/0)',
                _('% continuation bet 7th street'))
    
def ffreq1(stat_dict, player):
    stat_descriptions["ffreq1"] = _("% fold frequency flop/4th street") + " (ffreq1)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_freq_1'])/float(stat_dict[player]['was_raised_1'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'ff1=%3.1f%%'   % (100.0*stat),
                'ff_1=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['f_freq_1'], stat_dict[player]['was_raised_1']),
                _('% fold frequency flop/4th street'))
    except:
        return (stat,
                'NA',
                'ff1=NA',
                'ff_1=NA',
                '(0/0)',
                _('% fold frequency flop/4th street'))
    
def ffreq2(stat_dict, player):
    stat_descriptions["ffreq2"] = _("% fold frequency turn/5th street") + " (ffreq2)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_freq_2'])/float(stat_dict[player]['was_raised_2'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'ff2=%3.1f%%'   % (100.0*stat),
                'ff_2=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['f_freq_2'], stat_dict[player]['was_raised_2']),
                _('% fold frequency turn/5th street'))
    except:
        return (stat,
                'NA',
                'ff2=NA',
                'ff_2=NA',
                '(0/0)',
                _('% fold frequency turn/5th street'))
    
def ffreq3(stat_dict, player):
    stat_descriptions["ffreq3"] = _("% fold frequency river/6th street") + " (ffreq3)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_freq_3'])/float(stat_dict[player]['was_raised_3'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'ff3=%3.1f%%'   % (100.0*stat),
                'ff_3=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['f_freq_3'], stat_dict[player]['was_raised_3']),
                _('% fold frequency river/6th street'))
    except:
        return (stat,
                'NA',
                'ff3=NA',
                'ff_3=NA',
                '(0/0)',
                _('% fold frequency river/6th street'))
    
def ffreq4(stat_dict, player):
    stat_descriptions["ffreq4"] = _("% fold frequency 7th street") + " (ffreq4)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_freq_4'])/float(stat_dict[player]['was_raised_4'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'ff4=%3.1f%%'   % (100.0*stat),
                'ff_4=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['f_freq_4'], stat_dict[player]['was_raised_4']),
                _('% fold frequency 7th street'))
    except:
        return (stat,
                'NA',
                'ff4=NA',
                'ff_4=NA',
                '(0/0)',
                _('% fold frequency 7th street'))
        
def f_cb1(stat_dict, player):
    stat_descriptions["f_cb1"] = _("% fold to continuation bet flop/4th street") + " (f_cb1)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_cb_1'])/float(stat_dict[player]['f_cb_opp_1'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'f_cb1=%3.1f%%'   % (100.0*stat),
                'f_cb_1=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['f_cb_1'], stat_dict[player]['f_cb_opp_1']),
                _('% fold to continuation bet flop/4th street'))
    except:
        return (stat,
                'NA',
                'f_cb1=NA',
                'f_cb_1=NA',
                '(0/0)',
                _('% fold to continuation bet flop/4th street'))
    
def f_cb2(stat_dict, player):
    stat_descriptions["f_cb2"] = _("% fold to continuation bet turn/5th street") + " (f_cb2)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_cb_2'])/float(stat_dict[player]['f_cb_opp_2'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'f_cb2=%3.1f%%'   % (100.0*stat),
                'f_cb_2=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['f_cb_2'], stat_dict[player]['f_cb_opp_2']),
                _('% fold to continuation bet turn/5th street'))
    except:
        return (stat,
                'NA',
                'f_cb2=NA',
                'f_cb_2=NA',
                '(0/0)',
                _('% fold to continuation bet turn/5th street'))
    
def f_cb3(stat_dict, player):
    stat_descriptions["f_cb3"] = _("% fold to continuation bet river/6th street") + " (f_cb3)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_cb_3'])/float(stat_dict[player]['f_cb_opp_3'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'f_cb3=%3.1f%%'   % (100.0*stat),
                'f_cb_3=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'       % (stat_dict[player]['f_cb_3'], stat_dict[player]['f_cb_opp_3']),
                _('% fold to continuation bet river/6th street'))
    except:
        return (stat,
                'NA',
                'f_cb3=NA',
                'f_cb_3=NA',
                '(0/0)',
                _('% fold to continuation bet river/6th street'))
    
def f_cb4(stat_dict, player):
    stat_descriptions["f_cb4"] = _("% fold to continuation bet 7th street") + " (f_cb4)"
    stat = 0.0
    try:
        stat = float(stat_dict[player]['f_cb_4'])/float(stat_dict[player]['f_cb_opp_4'])
        return (stat,
                '%3.1f'         % (100.0*stat),
                'f_cb4=%3.1f%%'   % (100.0*stat),
                'f_cb_4=%3.1f%%'  % (100.0*stat),
                '(%d/%d)'      % (stat_dict[player]['f_cb_4'], stat_dict[player]['f_cb_opp_4']),
                _('% fold to continuation bet 7th street'))
    except:
        return (stat,
                'NA',
                'f_cb4=NA',
                'f_cb_4=NA',
                '(0/0)',
                _('% fold to continuation bet 7th street'))


def game_abbr(stat_dict, player, hand_instance):
    stat_descriptions["game_abbr"] = _("Game abbreviation") + " (game_abbr)"
    stat = ''
    uniq = hand_instance.gametype['category'] + '.' + hand_instance.gametype['limitType']
    try:
        stat = {
                # ftp's 10-game with official abbreviations
                'holdem.fl': 'H',
                'studhilo.fl': 'E',
                'omahahi.pl': 'P',
                '27_3draw.fl': 'T',
                'razz.fl': 'R',
                'holdem.nl': 'N',
                'omahahilo.fl': 'O',
                'studhi.fl': 'S',
                '27_1draw.nl': 'K',
                'badugi.fl': 'B',
                # other common games with dubious abbreviations
                'fivedraw.fl': 'F',
                'fivedraw.pl': 'Fp',
                'fivedraw.nl': 'Fn',
                '27_3draw.pl': 'Tp',
                '27_3draw.nl': 'Tn',
                'badugi.pl': 'Bp',
                'badugi.hp': 'Bh',
                'omahahilo.pl': 'Op',
                'omahahilo.nl': 'On',
                'holdem.pl': 'Hp',
                'studhi.nl': 'Sn',
                }[uniq]
    except:
        # this shouldn't really happen
        stat = '?'
    return (stat,
            '%s' % stat,
            'game=%s' % stat,
            'game_abbr=%s' % stat,
            '(%s)' % stat,
            _('Game abbreviation'))

def blank(stat_dict, player):
    # blank space on the grid
    stat_descriptions["blank"] = "Blank"
    stat = " "
    return (" ", " ", " ", " ", " ", "<blank>")
                
def starthands(stat_dict, player, hand_instance):
    
    
    #summary of known starting hands+position
    # data volumes could get crazy here,so info is limited to hands
    # in the current HH file only
    
    # this info is NOT read from the cache, so does not obey aggregation
    # parameters for other stats
    
    #display shows 3 categories
    # PFcall - limp or coldcall preflop
    # PFaggr - raise preflop
    # PFdefBB - defended in BB
    
    # hand is shown, followed by position indicator
    # (b=SB/BB. l=Button/cutoff m=previous 3 seats to that, e=remainder)
    
    # due to screen space required for this stat, it should only
    # be used in the popup section i.e.
    # <pu_stat pu_stat_name="starthands"> </pu_stat>
    handid = int(hand_instance.handid_selected)
    stat_descriptions["starthands"] = _("starting hands at this table") + " (starting hands)"
    PFlimp=" PFlimp:"
    PFaggr=" PFaggr:"
    PFcar=" PFCaRa:"
    PFdefend=" PFdefBB:"
    count_pfl = count_pfa = count_pfc = count_pfd = 2
    
    c = Configuration.Config()
    db_connection = Database.Database(c)
    sc = db_connection.get_cursor()

    sc.execute(("SELECT distinct startCards, street0Aggr, street0CalledRaiseDone, " +
    			"case when HandsPlayers.position = 'B' then 'b' " +
                            "when HandsPlayers.position = 'S' then 'b' " +
                            "when HandsPlayers.position = '0' then 'l' " +
                            "when HandsPlayers.position = '1' then 'l' " +
                            "when HandsPlayers.position = '2' then 'm' " +
                            "when HandsPlayers.position = '3' then 'm' " +
                            "when HandsPlayers.position = '4' then 'm' " +
                            "when HandsPlayers.position = '5' then 'e' " +
                            "when HandsPlayers.position = '6' then 'e' " +
                            "when HandsPlayers.position = '7' then 'e' " +
                            "when HandsPlayers.position = '8' then 'e' " +
                            "when HandsPlayers.position = '9' then 'e' " +
                            "else 'X' end " +
                        "FROM Hands, HandsPlayers, Gametypes " +
                        "WHERE HandsPlayers.handId = Hands.id " +
                        " AND Gametypes.id = Hands.gametypeid "+
                        " AND Gametypes.type = " +
                        "   (SELECT Gametypes.type FROM Gametypes, Hands   " +
                        "  WHERE Hands.gametypeid = Gametypes.id and Hands.id = %d) " +
                        " AND Gametypes.Limittype =  " +
                        "   (SELECT Gametypes.limitType FROM Gametypes, Hands  " +
                        " WHERE Hands.gametypeid = Gametypes.id and Hands.id = %d) " +
                        "AND Gametypes.category = 'holdem' " +
                        "AND fileId = (SELECT fileId FROM Hands " +
                        " WHERE Hands.id = %d) " +
                        "AND HandsPlayers.playerId = %d " +
                        "AND street0VPI " +
                        "AND startCards > 0 " +
                        "ORDER BY startCards DESC " +
                        ";")
                         % (int(handid), int(handid), int(handid), int(player)))

    for (qstartcards, qstreet0Aggr, qstreet0CalledRaiseDone, qposition) in sc.fetchall():
        humancards = Card.decodeStartHandValue("holdem", qstartcards)
                
        if qposition == "B" and qstreet0Aggr == False:
            PFdefend=PFdefend+"/"+humancards
            count_pfd += 1
            if (count_pfd / 8.0 == int(count_pfd / 8.0)):
                PFdefend=PFdefend+"\n"
        elif qstreet0Aggr == True:
            PFaggr=PFaggr+"/"+humancards+"."+qposition
            count_pfa += 1
            if (count_pfa / 8.0 == int(count_pfa / 8.0)):
                PFaggr=PFaggr+"\n"
        elif qstreet0CalledRaiseDone:
            PFcar=PFcar+"/"+humancards+"."+qposition
            count_pfc += 1
            if (count_pfc / 8.0 == int(count_pfc / 8.0)):
                PFcar=PFcar+"\n"
        else:
            PFlimp=PFlimp+"/"+humancards+"."+qposition
            count_pfl += 1
            if (count_pfl / 8.0 == int(count_pfl / 8.0)):
                PFlimp=PFlimp+"\n"
    sc.close()
    
    returnstring = PFlimp + "\n" + PFaggr + "\n" + PFcar + "\n" + PFdefend  #+ "\n" + str(handid)

    return ((returnstring),
            (returnstring),
            (returnstring),
            (returnstring),
            (returnstring),
            (''))

                
def build_stat_descriptions(stats_file):
    for method in dir(stats_file):
        if method in ("Charset", "Configuration", "Database", "GInitiallyUnowned", "gtk", "pygtk",
                        "player", "c", "db_connection", "do_stat", "do_tip", "stat_dict", "h", "re",
                        "re_Percent", "re_Places", "L10n", "sys", "_", "log", "encoder", "codecs",
                        "logging"):
            continue
        if method.startswith('__'):
            continue
        try:
            eval(method+"(None, None)")
        except:
            pass
    
    return stat_descriptions

if __name__== "__main__":
    statlist = dir()
    misslist = [ "Configuration", "Database", "Charset", "codecs", "encoder"
                 , "do_stat", "do_tip", "GInitiallyUnowned", "gtk", "pygtk", "Card"
                 , "L10n", "_", "__stat_override", "build_stat_descriptions", "log"
                 , "logging", "stat_descriptions", 'Decimal', 'GFileDescriptorBased'
                 , 'GPollableInputStream', 'GPollableOutputStream', 'calculate_end_stack'
                 , "re", "re_Places", 'Hand'
               ]
    statlist = [ x for x in statlist if x not in dir(sys) ]
    statlist = [ x for x in statlist if x not in dir(codecs) ]
    statlist = [ x for x in statlist if x not in misslist ]
    #print "statlist is", statlist

    c = Configuration.Config()
    db_connection = Database.Database(c)
    h = db_connection.get_last_hand()
    stat_dict = db_connection.get_stats_from_hand(h, "ring")
    print stat_dict
    hand_instance = Hand.hand_factory(h, c, db_connection)
    
    for player in stat_dict.keys():
        print (_("Example stats. Player = %s, Hand = %s:") % (player, h))
        for attr in statlist:
            print "  ", do_stat(stat_dict, player=player, stat=attr, hand_instance=hand_instance)
        break

    print _("Legal stats:")
    print _("(add _0 to name to display with 0 decimal places, _1 to display with 1, etc)")
    for attr in statlist:
        print "%-14s %s" % (attr, eval("%s.__doc__" % (attr)))
#        print "            <pu_stat pu_stat_name = \"%s\"> </pu_stat>" % (attr)
    print

    #db_connection.close_connection

