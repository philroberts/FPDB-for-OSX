import imaplib
import Configuration
import os
import pprint

pp = pprint.PrettyPrinter(indent=4)

def open_imap_connection(verbose=False):
    # Read the config file
    # FIXME
    hostname = 'imap.gmail.com'
    port = 993
    username = 'slartibartfast'
    password = '42'

    # Connect 
    if verbose: print "Connecting to %s" % hostname
    connection = imaplib.IMAP4_SSL(hostname)

    # Login to our account
    if verbose: print "Logging in as %s" % username
    connection.login(username, password)
    return connection

if __name__ == '__main__':
    # Read the config file
    # FIXME
    folder = "INBOX"
    c = open_imap_connection(verbose=True)

    try:
        typ, data = c.list(directory=folder)
        print typ, data

        c.select('INBOX', readonly=True)

        typ, msg_ids = c.search(None, '(SUBJECT "Results for PokerStars Tournament *")')
        print typ, msg_ids
        msgidlist = msg_ids[0].split(' ')
        print msgidlist

        for msg in msgidlist:
            print 'HEADER:'
            typ, msg_data = c.fetch(msg, '(BODY.PEEK[HEADER])')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    print response_part[1]
    
            print 'BODY TEXT:'
            typ, msg_data = c.fetch(msg, '(BODY.PEEK[TEXT])')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    print response_part[1]


    finally:
        try:
            c.close()
        except:
            pass
        c.logout()
