#!/bin/sh

#!/bin/bash

if [ $# -eq 0 ]; then
  echo "Usage: $0 <foldername> (e.g., $0 2024-01)"
  exit 1
fi

folder=$1

files=()
for file in *; do
	if [[ ${file} == "delta-$folder-"*".tex" && ${file} != *"-pandoc.tex" && ${file} != *"-tikz.tex" ]]; then
	    files+=("$file")
	fi
done

commands=()
for file in "${files[@]}"
do
	newname=$(basename "$file")

	echo ""
	echo "[ --------------- $file ----------------- ]"

	echo "Running: convert-py-2-html.py"

	command="python convert-py-2-html.py $folder-figures $file"
	echo "$command"
	eval "$command"

	commands+=("$command")
done

echo ""
echo "## FULL LIST OF CONVERT COMMANDS ##"

for command in "${commands[@]}"; do
    echo "$command"
done
