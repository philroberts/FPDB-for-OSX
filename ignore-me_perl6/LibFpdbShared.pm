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

module LibFpdbShared;
use v6;
#use strict;

class Util {
	method debug(Str $string) {
	#todo: i think this should be sub since its a class method not an instance method
		say "debug notice: ", $string;
	}#end debug_msg
	
	sub warn(Str $string) {
		say "todo: Util.warning";
	}#end warning
	
	sub fatal(Str $string, Database $db) {
		say "todo: Util.fatal_error";
	}#end fatal_error
}#end class Util

class Database {
	has Str $backend;
	has Str $host;
	has Str $name;
	has Str $user;
	my Str $password;
	submethod BUILD (Str $!backend, Str $!host, Str $!name, Str $!user, Str $!password) {
		Util.debug("running Database.BUILD");
		self.connect();
	}#end new Database
	
	our method connect() {
		say "todo: db.connect";
	}#end connect
	
	method disconnect() {
		say "todo: db.disconnect";
	}#end disconnect
	
	method cancel_import() {
		say "todo: db.cancel_import";
	}#end cancel_import
	
	my method drop_tables() {
		#todo: make this one private
		say "todo: db.drop_tables";
	}#end drop_tables
	
	method recreate_tables() {
		say "todo: db.recreate_tables";
	}#end recreate_tables
	
	#returns the id of the insert
	our Int method insert(Str $sql_command) {
		#todo: is it a bug that i need the "our" above?
		say "todo: db.insert";
		return 0;
	}#end insert
	
	our Str method fetch(Str $sql_command) {
		say "todo: db.fetch";
	}#end fetch
	
	our Bool method is_connected() {
		say "todo: db.is_connected";
	}#end 
}#end class Database

