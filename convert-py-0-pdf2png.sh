#!/bin/bash

# Check if pdftoppm is installed
if ! command -v magick &>/dev/null; then
    echo "Imagemagick (convert) is not installed. Please install it first."
    exit 1
fi

dir="$1"

prefix=""
if [ "$#" == 2 ]; then
	prefix="$2"
fi

count=0
for pdf_file in "$dir"/$prefix*\.pdf; do
    if [ -f "$pdf_file" ]; then
		let count+=1
		if (( count % 10 == 0 )); then
			 echo "PDF->PNG: $count converted..."
		fi
		
        filename=$(basename -- "$pdf_file")
        filename_noext="${filename%.*}"
        png_output="$dir/$filename_noext.png"

        magick "$pdf_file" -density 600 -transparent white -colorspace sRGB -limit memory 64MB -limit map 128MB "$png_output"
		
		if [ ! -f "$png_output" ] ; then
			echo "Failed to convert: $pdf_file to $png_output"
		 fi

    fi
done
echo "PDF->PNG: DONE!"
