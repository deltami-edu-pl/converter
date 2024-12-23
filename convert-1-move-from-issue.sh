#!/bin/bash

if [ $# -eq 0 ]; then
  echo "Usage: $0 <foldername> (e.g., $0 2024-01)"
  exit 1
fi

folder=$1

if [ ! -d $folder ]; then
	echo "ERROR: Folder $folder does not exist!"
	exit 1
fi

if [ ! -f "$folder/$folder-delta.tex" ]; then
	echo "ERROR: File $folder/$folder-delta.tex does not exist!"
	exit 1
fi

if [ ! -d $folder-figures ]; then
	echo "Creating directory $folder-figures"
	mkdir -p $folder-figures
fi

echo "# Copying images from folders 0-Tikz-figures, art, rys, ilustracje and stale"
cp $folder/0-Tikz-figures/* $folder-figures
cp $folder/art/* $folder-figures
cp $folder/rys/* $folder-figures
cp $folder/ilustracje/* $folder-figures
cp $folder/stale/* $folder-figures
filecount=`ls $folder-figures/*.pdf | wc -l`
echo "# Converting all pdf files to png (number of files: $filecount)"
bash convert-py-0-pdf2png.sh $folder-figures

files=()

while IFS= read -r -d '' file; do
  files+=("$file")
done < <(find "$folder" -regex '.*/[0-9][0-9]-.*tex' ! -name '00-spis.tex' -print0 | sort -z)

echo "# Creating files (merging $folder-delta.tex with 05-something.tex)"

commands=()
for line in "${files[@]}"
do
	filename=$(basename "$line")
	newname="delta-$folder-art-$filename"
	
	echo "Creating $newname"
	python convert-py-1-move-from-issue.py $folder/$folder-delta.tex $folder/$filename $newname $folder-figures
done
