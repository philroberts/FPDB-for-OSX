cd ..
rm *.pyc

echo "creating template po file"
python /usr/share/doc/python-2.*/examples/Tools/i18n/pygettext.py --output-dir=locale --default-domain=fpdb --output=fpdb-en_GB.pot *.py *.pyw

echo "merging template with existing translations"
msgmerge --update locale/fpdb-de_DE.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-es_ES.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-fr_FR.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-hu_HU.po locale/fpdb-en_GB.pot

echo "compiling mo files"
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/de/LC_MESSAGES/fpdb.mo locale/fpdb-de_DE.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/es/LC_MESSAGES/fpdb.mo locale/fpdb-es_ES.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/fr/LC_MESSAGES/fpdb.mo locale/fpdb-fr_FR.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/hu/LC_MESSAGES/fpdb.mo locale/fpdb-hu_HU.po

pocount locale/*.po
