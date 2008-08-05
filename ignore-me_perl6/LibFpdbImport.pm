#!/usr/bin/pugs

#Copyright 2008 Steffen Jobbagy-Felso
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in
#agpl-3.0.txt in the docs folder of the package.

module LibFpdbImport;
use v6;
#use strict;
use LibFpdbShared;
#use LibFpdbImport2;

class Player {
	has Str $name;
	has Int $start_cash;
	has Card @.cards;
	has Char $position;
	
	submethod BUILD (Str @strings) {
		say "todo: implement Player.BUILD";
	}#end Player.BUILD
	
	our Player method find_players(@strings) {
	#todo: i think this should be sub since its a class method not an instance method
		say "todo: implement Player.find_players";
	}
}#end class Player

class Line {
	has Str $line;
	has Bool $processed;
	
	our protected submethod BUILD() {
		say "todo: implement Line.BUILD?"
	}#end Line.BUILD
	
	our Line method recognise_and_parse(@strings) {
	#todo: i think this should be sub since its a class method not an instance method
		say "todo: implement Line.recognise_and_parse";
	}#end Line.recognise_and_parse
}#end class Line

class ActionLine is Line {
	has Player $player;
	has Str $type;
	has Int $amount;
	has Bool $all_in;
	has Int $action_no;
}#end class ActionLine

class WinLine is Line {
	has Player $player;
	has Int $amount;
}#end class WinLine

class RakeLine is Line {
	has Int $amount;
}#end class RakeLine

class CardLine is Line {
	has Bool $board_line;
	has Player $player;
	has Card @cards;
}#end class CardLine

#for useless lines
class CrapLine is Line {
	has Str $type;
}#end class CrapLine

class Hand {
	has Line @.lines;
	#has Str @strings;
	has Site $site;
	has Str $currency;

	has Str $type;
	has Str $category;
	has Str $limit_type;#todo: above ; missing causes error, but that doesnt list ; as a possibility
	has Player @.players;
	has Card @.board;
	has Int $db_id;
	
	submethod BUILD(Str @strings) {
		Util.debug("running Hand.BUILD");
		say "strings:",@strings;
		#this contructor automatically parses the hand. call .store for storing
		
		@.players=Player.find_players(@strings);
		@.lines=Line.recognise_and_parse(@strings);
		
		for @strings -> $line {
			if class_of(line)==CardLine {
				if line.board {
					board=line.cards;
				} else {
					for player in players {
						if line.player==player {
							player.cards=line.cards;
						}
					}
				}
			}
		}
	}#end Hand.BUILD
	
	our Bool method is_holdem(){
		if category==("holdem"|"omahahi"|"omahahilo") {
			return True;
		} else {
			return False;
		}
	}#end Hand.is_holdem
	
	our Bool method is_stud(){
		return not is_holdem();
	}#end Hand.is_stud
	
	our Bool method store($db) {
		say "todo: Hand.store";
	}#end Hand.store
}#end class Hand

class Importer {
#todo: be Thread?
	submethod BUILD (Database $db, Str $filename) {
		Util.debug("running Importer.BUILD");
		if (not ($db.is_connected())) {
			Util.fatal("not connected to DB");
		}
		
		my IO $?filehandle=$filename;
		#for =$filehandle -> $line {say $line}
		my Str @lines =$filehandle;
		
		my Int $hand_start=0;
		my Int $hand_end=0;
		my Int $loopcount=0;
		loop {#one loop of this per hand
			$loopcount++;
			say "loopcount", $loopcount;
			my Int $current_line_index=$hand_end+1; #previous hand end is new hand start
			for (my Int $i, $i<5, $i++) {#remove blank hands
				if (@lines[$current_line_index].bytes) < 6 {
					$current_line_index++;
				} else {
					$hand_start=$current_line_index;
					break;
				}
			}
			my Bool $continue=True; #todo: this is dumb, find out correct loop
			while $continue {#loop through the lines to find end of hand
				$current_line_index++;
				if (@lines[$current_line_index].bytes) < 6 {
					$hand_end=$current_line_index;
					$continue=False;
				}
			}#end of find end of hand loop
			my Str @handlines=@lines[$hand_start..$hand_end];
			my Hand $hand .= new(:lines(@handlines));
			$hand.store($db);
			say "todo: record \$db_id";
			say "todo: terminate on EOF";
		}
	}#end new Importer
}#end class Importer

