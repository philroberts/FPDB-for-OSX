# pokerstars_cash.py
# -*- coding: iso-8859-15
#
# PokerStats, an online poker statistics tracking software for Linux
# Copyright (C) 2007-2008 Mika Boström <bostik@iki.fi>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
from errors import *
import re
import regex

# These are PokerStars specific;
# More importantly, they are currently valid for cash game only.
#####
# XXX: There was a weird problem with saved hand histories in PokerStars
# client 2.491; if a user was present on the table (and thus anywhere in
# the hand history), with non-standard characters in their username, the
# client would prepend a literal Ctrl-P (ASCII 16, 0x10) character to
# the hand history title line. Hence, to allow these strangely saved
# hands to be parsed and imported, there is a conditional "one extra
# character" allowed at the start of the new hand regex.
__NEW_HAND_REGEX='^.?PokerStars Game #\d+:\s+Hold\'em'
__HAND_INFO_REGEX='^.*#(\d+):\s+(\S+)\s([\s\S]+)\s\(\$?([.0-9]+)/\$?([.0-9]+)\)\s-\s(\S+)\s-?\s?(\S+)\s\(?(\w+)\)?'
__TABLE_INFO_REGEX='^\S+\s+\'.*\'\s+(\d+)-max\s+Seat\s#(\d+)'
__PLAYER_INFO_REGEX='^Seat\s(\d+):\s(.*)\s\(\$?([.\d]+)\s'
__POST_SB_REGEX='^(.*):\sposts small blind'
__POST_BB_REGEX='^(.*):\sposts big blind'
__POST_BOTH_REGEX='^(.*):\sposts small & big blinds'
__HAND_STAGE_REGEX='^\*{3}\s(.*)\s\*{3}'
__HOLE_CARD_REGEX='^\*{3}\sHOLE CARDS'
__FLOP_CARD_REGEX='^\*{3}\sFLOP\s\*{3}\s\[(\S{2})\s(\S{2})\s(\S{2})\]'
__TURN_CARD_REGEX='^\*{3}\sTURN\s\*{3}\s\[\S{2}\s\S{2}\s\S{2}\]\s\[(\S{2})\]'
__RIVER_CARD_REGEX='^\*{3}\sRIVER\s\*{3}\s\[\S{2}\s\S{2}\s\S{2}\s\S{2}\]\s\[(\S{2})\]'
__SHOWDOWN_REGEX='^\*{3}\sSHOW DOWN'
__SUMMARY_REGEX='^\*{3}\sSUMMARY'
__UNCALLED_BET_REGEX='^Uncalled bet \(\$([.\d]+)\) returned to (.*)'
__POT_AND_RAKE_REGEX='^Total\spot\s\$([.\d]+).*\|\sRake\s\$([.\d]+)'
__COLLECT_POT_REGEX='^(.*)\scollected\s\$([.\d]+)\sfrom\s((main|side)\s)?pot'
__POCKET_CARDS_REGEX='^Dealt\sto\s(.*)\s\[(\S{2})\s(\S{2})\]'
__SHOWN_CARDS_REGEX='^(.*):\sshows\s\[(\S{2})\s(\S{2})\]'
__ACTION_STEP_REGEX='^(.*):\s(bets|checks|raises|calls|folds)((\s\$([.\d]+))?(\sto\s\$([.\d]+))?)?'

__SHOWDOWN_ACTION_REGEX='^(.*):\s(shows|mucks)'
__SUMMARY_CARDS_REGEX='^Seat\s\d+:\s(.*)\s(showed|mucked)\s\[(\S{2})\s(\S{2})\]'
__SUMMARY_CARDS_EXTRA_REGEX='^Seat\s\d+:\s(.*)\s(\(.*\)\s)(showed|mucked)\s\[(\S{2})\s(\S{2})\]'


def regexes():
    m = regex.RegexMatch()
### Compile the regexes
    m.hand_start_re = re.compile(__NEW_HAND_REGEX)
    m.hand_info_re = re.compile(__HAND_INFO_REGEX)
    m.table_info_re = re.compile(__TABLE_INFO_REGEX)
    m.player_info_re = re.compile(__PLAYER_INFO_REGEX)
    m.small_blind_re = re.compile(__POST_SB_REGEX)
    m.big_blind_re = re.compile(__POST_BB_REGEX)
    m.both_blinds_re = re.compile(__POST_BOTH_REGEX)
    m.hand_stage_re = re.compile(__HAND_STAGE_REGEX)
    m.hole_cards_re = re.compile(__HOLE_CARD_REGEX)
    m.flop_cards_re = re.compile(__FLOP_CARD_REGEX)
    m.turn_card_re = re.compile(__TURN_CARD_REGEX)
    m.river_card_re = re.compile(__RIVER_CARD_REGEX)
    m.showdown_re = re.compile(__SHOWDOWN_REGEX)
    m.summary_re = re.compile(__SUMMARY_REGEX)
    m.uncalled_bet_re = re.compile(__UNCALLED_BET_REGEX)
    m.collect_pot_re = re.compile(__COLLECT_POT_REGEX)
    m.pocket_cards_re = re.compile(__POCKET_CARDS_REGEX)
    m.cards_shown_re = re.compile(__SHOWN_CARDS_REGEX)
    m.summary_cards_re = re.compile(__SUMMARY_CARDS_REGEX)
    m.summary_cards_extra_re = re.compile(__SUMMARY_CARDS_EXTRA_REGEX)
    m.action_re = re.compile(__ACTION_STEP_REGEX)
    m.rake_re = re.compile(__POT_AND_RAKE_REGEX)
    m.showdown_action_re = re.compile(__SHOWDOWN_ACTION_REGEX)
###
    return m

