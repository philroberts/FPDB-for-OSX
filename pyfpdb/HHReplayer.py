#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
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

import os, pygame
import time
from pygame.locals import *
from pygame.compat import geterror

import Charset

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, '.')

def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print ('Cannot load image:', fullname)
        print "data_dir: '%s' name: '%s'" %( data_dir, name)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()


def main():
    #Initialize Everything
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((640, 480))
    table_no = 1
    table_title = "Valparaíso / aaaaaaaaaaaaaaaaa"
    pygame.display.set_caption(Charset.to_utf8(table_title))
    pygame.mouse.set_visible(0)

    # Load background image
    bgimage, rect = load_image('../gfx/Table.png')
    background = pygame.Surface(screen.get_size())
    background.blit(bgimage, (0, 0))

    #Put Text On The Background, Centered
    if pygame.font:
        font = pygame.font.Font(None, 24)
        text = font.render("Yarmouth Texas Hold'em NL -$0.01/$0.02", 1, (10, 10, 10))
        textpos = text.get_rect(centerx=background.get_width()/2)
        background.blit(text, textpos)

    #Display The Background
    screen.blit(background, (0, 0))
    pygame.display.flip()

    going = True
    while going:
        clock.tick(6000)
        # Draw 
        screen.blit(background, (0, 0))
        # Change table #
        #table_no += 1
        #table_title = "Tournament 2010090009 Table %s - Blinds $600/$1200 Anto $150" % table_no
        #pygame.display.set_caption(table_title)
        time.sleep(10)

    
if __name__ == '__main__':
    main()

