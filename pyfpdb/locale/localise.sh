cd ..
rm *.pyc

echo "creating template po file"
python /usr/share/doc/python-2.*/examples/Tools/i18n/pygettext.py --output-dir=locale --default-domain=fpdb --output=fpdb-en_GB.pot *.py *.pyw

echo "merging template with existing translations"
#msgmerge --update locale/fpdb-.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-de_DE.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-es_ES.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-fr_FR.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-hu_HU.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-it_IT.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-pl_PL.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-pt_BR.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-ru_RU.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-zh_CN.po locale/fpdb-en_GB.pot

echo "checking translated files"
#msgfmt -c --check-accelerators locale/fpdb-.po
msgfmt -c --check-accelerators locale/fpdb-de_DE.po
msgfmt -c --check-accelerators locale/fpdb-es_ES.po
msgfmt -c --check-accelerators locale/fpdb-fr_FR.po
msgfmt -c --check-accelerators locale/fpdb-hu_HU.po
msgfmt -c --check-accelerators locale/fpdb-it_IT.po
msgfmt -c --check-accelerators locale/fpdb-pl_PL.po
msgfmt -c --check-accelerators locale/fpdb-pt_BR.po
msgfmt -c --check-accelerators locale/fpdb-ru_RU.po
msgfmt -c --check-accelerators locale/fpdb-zh_CN.po

echo "check the following output for misplaced \\\\"
grep "[\\][\\]" locale/*.po

echo "compiling mo files"
#python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale//LC_MESSAGES/fpdb.mo locale/fpdb-.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/de/LC_MESSAGES/fpdb.mo locale/fpdb-de_DE.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/es/LC_MESSAGES/fpdb.mo locale/fpdb-es_ES.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/fr/LC_MESSAGES/fpdb.mo locale/fpdb-fr_FR.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/hu/LC_MESSAGES/fpdb.mo locale/fpdb-hu_HU.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/it/LC_MESSAGES/fpdb.mo locale/fpdb-it_IT.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/pl/LC_MESSAGES/fpdb.mo locale/fpdb-pl_PL.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/pt/LC_MESSAGES/fpdb.mo locale/fpdb-pt_BR.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/ru/LC_MESSAGES/fpdb.mo locale/fpdb-ru_RU.po
python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale/zh/LC_MESSAGES/fpdb.mo locale/fpdb-zh_CN.po

pocount locale/*.po
