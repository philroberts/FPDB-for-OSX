cd ..
rm *.pyc

echo "creating template po file"
pygettext --output-dir=locale --default-domain=fpdb --output=fpdb-en_GB.pot *.py *.pyw

echo "merging template with existing translations"
#msgmerge --update locale/fpdb-.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-ca_ES.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-de_DE.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-es_ES.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-fr_FR.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-hu_HU.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-it_IT.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-ja_JP.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-lt_LT.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-nl_NL.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-pl_PL.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-pt_BR.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-ro_RO.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-ru_RU.po locale/fpdb-en_GB.pot
msgmerge --update locale/fpdb-zh_CN.po locale/fpdb-en_GB.pot

echo "checking translated files"
#msgfmt -c --check-accelerators locale/fpdb-.po
msgfmt -c --check-accelerators locale/fpdb-ca_ES.po
msgfmt -c --check-accelerators locale/fpdb-de_DE.po
msgfmt -c --check-accelerators locale/fpdb-es_ES.po
msgfmt -c --check-accelerators locale/fpdb-fr_FR.po
msgfmt -c --check-accelerators locale/fpdb-hu_HU.po
msgfmt -c --check-accelerators locale/fpdb-it_IT.po
msgfmt -c --check-accelerators locale/fpdb-ja_JP.po
msgfmt -c --check-accelerators locale/fpdb-lt_LT.po
msgfmt -c --check-accelerators locale/fpdb-nl_NL.po
msgfmt -c --check-accelerators locale/fpdb-pl_PL.po
msgfmt -c --check-accelerators locale/fpdb-pt_BR.po
msgfmt -c --check-accelerators locale/fpdb-ro_RO.po
msgfmt -c --check-accelerators locale/fpdb-ru_RU.po
msgfmt -c --check-accelerators locale/fpdb-zh_CN.po

echo "check the following output for misplaced \\\\"
grep -n "[\\][\\]" locale/*.po

echo "compiling mo files"
#python /usr/share/doc/python-2.*/examples/Tools/i18n/msgfmt.py --output-file=locale//LC_MESSAGES/fpdb.mo locale/fpdb-.po
msgfmt --output-file=locale/ca/LC_MESSAGES/fpdb.mo locale/fpdb-ca_ES.po
msgfmt --output-file=locale/de/LC_MESSAGES/fpdb.mo locale/fpdb-de_DE.po
msgfmt --output-file=locale/es/LC_MESSAGES/fpdb.mo locale/fpdb-es_ES.po
msgfmt --output-file=locale/fr/LC_MESSAGES/fpdb.mo locale/fpdb-fr_FR.po
msgfmt --output-file=locale/hu/LC_MESSAGES/fpdb.mo locale/fpdb-hu_HU.po
msgfmt --output-file=locale/it/LC_MESSAGES/fpdb.mo locale/fpdb-it_IT.po
msgfmt --output-file=locale/ja/LC_MESSAGES/fpdb.mo locale/fpdb-ja_JP.po
msgfmt --output-file=locale/lt/LC_MESSAGES/fpdb.mo locale/fpdb-lt_LT.po
msgfmt --output-file=locale/nl/LC_MESSAGES/fpdb.mo locale/fpdb-nl_NL.po
msgfmt --output-file=locale/pl/LC_MESSAGES/fpdb.mo locale/fpdb-pl_PL.po
msgfmt --output-file=locale/pt/LC_MESSAGES/fpdb.mo locale/fpdb-pt_BR.po
msgfmt --output-file=locale/ro/LC_MESSAGES/fpdb.mo locale/fpdb-ro_RO.po
msgfmt --output-file=locale/ru/LC_MESSAGES/fpdb.mo locale/fpdb-ru_RU.po
msgfmt --output-file=locale/zh/LC_MESSAGES/fpdb.mo locale/fpdb-zh_CN.po

pocount locale/*.po
rm locale/*~
rm messages.mo
