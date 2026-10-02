#!/bin/bash
# Script to generate po files outside of the normal build process
#
# Pre-requisite:
# The following tools must be installed on your system and accessible from path
# gawk, find, xgettext, sed (gsed on Mac OSX), msguniq, msgmerge, msgattrib, msgfmt, msginit
#
# Run this script from within the locale folder.
#
# Author: Pr2
# Version: 1.4 - runs on Linux (GNU find/sed) and Mac OSX, checks the gettext tools up front,
#                no guessed (fuzzy) translations, no source locations, leaves all files as they
#                are when only the POT-Creation-Date header changed
PluginName=SubsSupport
localgsed="sed"
findoptions=""

if [[ "$OSTYPE" == "darwin"* ]]; then
	# Mac OSX
	printf "Script running on Mac OSX [%s]\n" "$OSTYPE"
	findoptions=" -s -X "
	localgsed="gsed"
fi

for tool in gawk xgettext msguniq msgmerge msgattrib msgfmt msginit; do
	if ! command -v $tool > /dev/null 2>&1; then
		printf "Error: '%s' not found in PATH - install the gettext tools first.\n" "$tool" >&2
		exit 1
	fi
done

printf "Po files update/creation from script starting.\n"
#
# Retrieve languages from Makefile.am LANGS variable for backward compatibility
#
languages=($(gawk ' BEGIN { FS=" " }
		/^LANGS/ {
			for (i=3; i<=NF; i++)
				printf "%s ", $i
		} ' Makefile.am ))

#
# Arguments to generate the pot and po files are not retrieved from the Makefile.
# So if parameters are changed in Makefile please report the same changes in this script.
#

if [[ -f $PluginName.pot ]]; then
	cp $PluginName.pot $PluginName.pot.bak
fi

printf "Creating temporary file $PluginName-py.pot\n"
find $findoptions ../plugin/ -name "*.py" -exec xgettext --no-wrap -L Python --from-code=UTF-8 -kpgettext:1c,2 -kN_ --add-comments="TRANSLATORS:" -d $PluginName -s -o $PluginName-py.pot {} \+
$localgsed --in-place $PluginName-py.pot --expression=s/CHARSET/UTF-8/
printf "Creating: $PluginName.pot\n"
msguniq --no-wrap --no-location -o $PluginName.pot $PluginName-py.pot
rm $PluginName-py.pot

# only the POT-Creation-Date changed: keep the old pot, po files stay untouched
if [[ -f $PluginName.pot.bak ]]; then
	grep -v '^"POT-Creation-Date:' $PluginName.pot > $PluginName.pot.new
	grep -v '^"POT-Creation-Date:' $PluginName.pot.bak > $PluginName.pot.old
	if diff -q $PluginName.pot.old $PluginName.pot.new > /dev/null; then
		printf "No string changes (only POT-Creation-Date) - leaving all files as they are.\n"
		mv $PluginName.pot.bak $PluginName.pot
		rm -f $PluginName.pot.old $PluginName.pot.new
		exit 0
	fi
	rm -f $PluginName.pot.bak $PluginName.pot.old $PluginName.pot.new
fi

OLDIFS=$IFS
IFS=" "
for lang in "${languages[@]}" ; do
	if [[ -f $lang.po ]]; then
		printf "Updating existing translation file %s.po\n" $lang
		msgmerge --backup=none --no-wrap --no-fuzzy-matching --no-location -U $lang.po $PluginName.pot && touch $lang.po
		msgattrib --no-wrap --no-obsolete $lang.po -o $lang.po
		msgfmt -o $lang.mo $lang.po
	else
		printf "New file created: %s.po, please add it to github before commit\n" $lang
		msginit -l $lang -o $lang.po -i $PluginName.pot --no-translator
		msgfmt -o $lang.mo $lang.po
	fi
done
IFS=$OLDIFS
printf "Po files update/creation from script finished!\n"
