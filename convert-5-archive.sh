#!/bin/bash

if [ $# -eq 0 ]; then
  echo "Usage: $0 <foldername> (e.g., $0 2024-01)"
  exit 1
fi

folder=$1

mkdir $folder-gotowe

mv $folder-figures $folder-gotowe
rm -r $folder
rm -r $folder-figures-not-used

mv delta-$folder* $folder-gotowe
