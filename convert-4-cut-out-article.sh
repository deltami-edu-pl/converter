#!/bin/bash

if [ $# -eq 0 ]; then
  echo "Usage: $0 <foldername> (e.g., $0 2024-01)"
  exit 1
fi

folder=$1

start_marker="<\!-- \\/\\/\\/\\/ START OF ARTICLE \\/\\/\\/\\/ -->"
end_marker="<\!-- \\/\\/\\/\\/ END OF ARTICLE \\/\\/\\/\\/ -->"

echo "For every article starting with delta-$folder-...html I cut out <article> element and replace 2024-07-figures to /media/2024-07-figures"

# Find all files starting with 'asd'
for file in *; do
	if [[ ${file} == "delta-$folder-"*".html" && ${file} != *"-pandoc.html" && ${file} != *"-article.html" ]]; then
	    if [[ -f $file ]]; then
            # Extract the part from START to END (inclusive)
            content=$(sed -n "/$start_marker/,/$end_marker/p" "$file")

            # Replace all occurrences of X with Y
            updated_content=$(echo "$content" | sed "s/$folder-figures/\/media\/$folder-figures/g")

            # Save the modified content to a new file
            new_file=${file/\.html/-article.html}
            echo "$updated_content" > "$new_file"
			echo "Created $new_file"
	    fi
	fi
done
