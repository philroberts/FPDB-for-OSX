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

# Modified for use in fpdb by Carl Gherardi

import re

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


class FpdbRegex:
	def __init__(self):
		self.__GAME_INFO_REGEX=''
		self.__SPLIT_HAND_REGEX='\n\n\n'
		self.__NEW_HAND_REGEX='^.?PokerStars Game #\d+:\s+Hold\'em'
		self.__HAND_INFO_REGEX='^.*#(\d+):\s+(\S+)\s([\s\S]+)\s\(\$?([.0-9]+)/\$?([.0-9]+)\)\s-\s(\S+)\s-?\s?(\S+)\s\(?(\w+)\)?'
		self.__TABLE_INFO_REGEX='^\S+\s+\'.*\'\s+(\d+)-max\s+Seat\s#(\d+)'
		self.__PLAYER_INFO_REGEX='^Seat\s(\d+):\s(.*)\s\(\$?([.\d]+)\s'
		self.__POST_SB_REGEX='^(.*):\sposts small blind'
		self.__POST_BB_REGEX='^(.*):\sposts big blind'
		self.__POST_BOTH_REGEX='^(.*):\sposts small & big blinds'
		self.__HAND_STAGE_REGEX='^\*{3}\s(.*)\s\*{3}'
		self.__HOLE_CARD_REGEX='^\*{3}\sHOLE CARDS'
		self.__FLOP_CARD_REGEX='^\*{3}\sFLOP\s\*{3}\s\[(\S{2})\s(\S{2})\s(\S{2})\]'
		self.__TURN_CARD_REGEX='^\*{3}\sTURN\s\*{3}\s\[\S{2}\s\S{2}\s\S{2}\]\s\[(\S{2})\]'
		self.__RIVER_CARD_REGEX='^\*{3}\sRIVER\s\*{3}\s\[\S{2}\s\S{2}\s\S{2}\s\S{2}\]\s\[(\S{2})\]'
		self.__SHOWDOWN_REGEX='^\*{3}\sSHOW DOWN'
		self.__SUMMARY_REGEX='^\*{3}\sSUMMARY'
		self.__UNCALLED_BET_REGEX='^Uncalled bet \(\$([.\d]+)\) returned to (.*)'
		self.__POT_AND_RAKE_REGEX='^Total\spot\s\$([.\d]+).*\|\sRake\s\$([.\d]+)'
		self.__COLLECT_POT_REGEX='^(.*)\scollected\s\$([.\d]+)\sfrom\s((main|side)\s)?pot'
		self.__HERO_CARDS_REGEX='^Dealt\sto\s(.*)\s\[(\S{2})\s(\S{2})\]'
		self.__SHOWN_CARDS_REGEX='^(.*):\sshows\s\[(\S{2})\s(\S{2})\]'
		self.__ACTION_STEP_REGEX='^(.*):\s(bets|checks|raises|calls|folds)((\s\$([.\d]+))?(\sto\s\$([.\d]+))?)?'

		self.__SHOWDOWN_ACTION_REGEX='^(.*):\s(shows|mucks)'
		self.__SUMMARY_CARDS_REGEX='^Seat\s\d+:\s(.*)\s(showed|mucked)\s\[(\S{2})\s(\S{2})\]'
		self.__SUMMARY_CARDS_EXTRA_REGEX='^Seat\s\d+:\s(.*)\s(\(.*\)\s)(showed|mucked)\s\[(\S{2})\s(\S{2})\]'

	def compileRegexes(self):
		### Compile the regexes
		self.game_info_re = re.compile(self.__GAME_INFO_REGEX)
		self.split_hand_re = re.compile(self.__SPLIT_HAND_REGEX)
		self.hand_start_re = re.compile(self.__NEW_HAND_REGEX)
		self.hand_info_re = re.compile(self.__HAND_INFO_REGEX)
		self.table_info_re = re.compile(self.__TABLE_INFO_REGEX)
		self.player_info_re = re.compile(self.__PLAYER_INFO_REGEX)
		self.small_blind_re = re.compile(self.__POST_SB_REGEX)
		self.big_blind_re = re.compile(self.__POST_BB_REGEX)
		self.both_blinds_re = re.compile(self.__POST_BOTH_REGEX)
		self.hand_stage_re = re.compile(self.__HAND_STAGE_REGEX)
		self.hole_cards_re = re.compile(self.__HOLE_CARD_REGEX)
		self.flop_cards_re = re.compile(self.__FLOP_CARD_REGEX)
		self.turn_card_re = re.compile(self.__TURN_CARD_REGEX)
		self.river_card_re = re.compile(self.__RIVER_CARD_REGEX)
		self.showdown_re = re.compile(self.__SHOWDOWN_REGEX)
		self.summary_re = re.compile(self.__SUMMARY_REGEX)
		self.uncalled_bet_re = re.compile(self.__UNCALLED_BET_REGEX)
		self.collect_pot_re = re.compile(self.__COLLECT_POT_REGEX)
		self.hero_cards_re = re.compile(self.__HERO_CARDS_REGEX)
		self.cards_shown_re = re.compile(self.__SHOWN_CARDS_REGEX)
		self.summary_cards_re = re.compile(self.__SUMMARY_CARDS_REGEX)
		self.summary_cards_extra_re = re.compile(self.__SUMMARY_CARDS_EXTRA_REGEX)
		self.action_re = re.compile(self.__ACTION_STEP_REGEX)
		self.rake_re = re.compile(self.__POT_AND_RAKE_REGEX)
		self.showdown_action_re = re.compile(self.__SHOWDOWN_ACTION_REGEX)

	# Set methods for plugins to override

	def setGameInfoRegex(self, string):
		self.__GAME_INFO_REGEX = string

	def setSplitHandRegex(self, string):
		self.__SPLIT_HAND_REGEX = string

	def setNewHandRegex(self, string):
		self.__NEW_HAND_REGEX = string

	def setHandInfoRegex(self, string):
		self.__HAND_INFO_REGEX = string

	def setTableInfoRegex(self, string):
		self.__TABLE_INFO_REGEX = string

	def setPlayerInfoRegex(self, string):
		self.__PLAYER_INFO_REGEX = string

	def setPostSbRegex(self, string):
		self.__POST_SB_REGEX = string

	def setPostBbRegex(self, string):
		self.__POST_BB_REGEX = string

	def setPostBothRegex(self, string):
		self.__POST_BOTH_REGEX = string

	def setHandStageRegex(self, string):
		self.__HAND_STAGE_REGEX = string

	def setHoleCardRegex(self, string):
		self.__HOLE_CARD_REGEX = string

	def setFlopCardRegex(self, string):
		self.__FLOP_CARD_REGEX = string

	def setTurnCardRegex(self, string):
		self.__TURN_CARD_REGEX = string

	def setRiverCardRegex(self, string):
		self.__RIVER_CARD_REGEX = string

	def setShowdownRegex(self, string):
		self.__SHOWDOWN_REGEX = string

	def setSummaryRegex(self, string):
		self.__SUMMARY_REGEX = string

	def setUncalledBetRegex(self, string):
		self.__UNCALLED_BET_REGEX = string

	def setCollectPotRegex(self, string):
		self.__COLLECT_POT_REGEX = string

	def setHeroCardsRegex(self, string):
		self.__HERO_CARDS_REGEX = string

	def setShownCardsRegex(self, string):
		self.__SHOWN_CARDS_REGEX = string

	def setSummaryCardsRegex(self, string):
		self.__SUMMARY_CARDS_REGEX = string

	def setSummaryCardsExtraRegex(self, string):
		self.__SUMMARY_CARDS_EXTRA_REGEX = string

	def setActionStepRegex(self, string):
		self.__ACTION_STEP_REGEX = string

	def setPotAndRakeRegex(self, string):
		self.__POT_AND_RAKE_REGEX = string

	def setShowdownActionRegex(self, string):
		self.__SHOWDOWN_ACTION_REGEX = string

