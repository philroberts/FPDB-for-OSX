
# create .bat scripts in windows to try out different gtk dirs

try:

    import os
    import sys
    import re

    if os.name != 'nt':
        print "\nThis script is only for windows\n"
        exit()

    dirs = re.split(os.pathsep, os.environ['PATH'])
    # remove any trailing / or \ chars from dirs:
    dirs = [re.sub('[\\/]$','',p) for p in dirs]
    # remove any dirs containing 'python' apart from those ending in 'python25', 'python26' or 'python':
    dirs = [p for p in dirs if not re.search('python', p, re.I) or re.search('python25$', p, re.I) or re.search('python26$', p, re.I)]
    # find gtk dirs:
    gtkdirs = [p for p in dirs if re.search('gtk', p, re.I)]

    lines = [ '@echo off\n\n'
            , '<path goes here>'
            , 'python fpdb.py\n\n'
            , 'pause\n\n'
            ]
    if gtkdirs:
        i = 1
        for gpath in gtkdirs:   # enumerate converts the \\ into \
            tmpdirs = [p for p in dirs if not re.search('gtk', p, re.I) or p == gpath]
            tmppath = ";".join(tmpdirs)
            lines[1] = 'PATH=' + tmppath + '\n\n'
            bat = open('run_fpdb'+str(i)+'.bat', 'w')
            bat.writelines(lines)
            bat.close()
            i = i + 1
    else:
        print "\nno gtk directories found in your path - install gtk or edit the path manually\n"

except SystemExit:
    pass

except:
    print "Error:", str(sys.exc_info())
    pass

# sys.stdin.readline()
