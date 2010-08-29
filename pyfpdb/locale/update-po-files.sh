#!/bin/sh

# Our master file
REFERENCE_PO=fpdb-en_GB.po

# Update all .po files
for po in *.po; do
    if [ ${po} != ${REFERENCE_PO} ]; then
        msgmerge --update ${po} ${REFERENCE_PO}
    fi
done

