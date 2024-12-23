#!/bin/bash

if [ $# -eq 0 ]; then
  echo "Usage: $0 <folder>"
  exit 1
fi

folder=$1

mkdir $folder-figures-used

for file in *; do
	if [[ ${file} == "delta-$folder-"*".tex" && ${file} != *"-pandoc.tex" && ${file} != *"-tikz.tex" ]]; then
		noext="${file%.*}"
		echo "Cleaning $noext..."

		rm -f $noext-tikz.*
		rm -f $noext-pandoc.*
		rm -f ${noext:18}.tex
		
		for file2 in *; do
			if [[ ${file2} == ${noext}* && ${file2} != $noext.tex && ${file2} != $noext.html ]]; then
				rm -f $file2
			fi
		done
		
		python convert-py-3-clean.py $noext.html $folder-figures $folder-figures-used
	fi
done

mv $folder-figures $folder-figures-not-used
mv $folder-figures-used $folder-figures