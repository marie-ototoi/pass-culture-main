#!/bin/sh

# Add version file to build
cat package.json | grep -E '"version": "[0-9]+.[0-9]+.[0-9]+"' | grep -Eo '[0-9]+.[0-9]+.[0-9]+' > build/version.txt
echo "Version copied to version.txt."
