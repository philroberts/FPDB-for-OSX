#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2009-2010 Carl Gherardi
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in agpl-3.0.txt.

import BetfairToFpdb
from Hand import *
import py

import Configuration
import Database
import SQL
import fpdb_import

config = Configuration.Config(file = "HUD_config.test.xml")
db = Database.Database(config)
sql = SQL.Sql(db_server = 'sqlite')

settings = {}
settings.update(config.get_db_parameters())
settings.update(config.get_tv_parameters())
settings.update(config.get_import_parameters())
settings.update(config.get_default_paths())

def testFlopImport():
    db.recreate_tables()
    importer = fpdb_import.Importer(False, settings, config)
    importer.setDropIndexes("don't drop")
    importer.setFailOnError(True)
    importer.setThreads(-1)
    importer.addBulkImportImportFileOrDir(
            """regression-test-files/cash/Betfair/Flop/PLO-6max-USD-0.05-0.10-200909.All.in.river.splitpot.txt""", site="Betfair")
    importer.setCallHud(False)
    (stored, dups, partial, errs, ttime) = importer.runImport()
    importer.clearFileList()

    # Should actually do some testing here
    assert 1 == 1
