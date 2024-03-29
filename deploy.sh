#!/bin/bash

# Read current version
version=$(sed -nE 's/pkgver=([0-9]+\.[0-9]+)/\1/p' arch-packages/client/PKGBUILD)

# Check if version was captured
if [ -z "$version" ]; then
    echo "Version not found."
    exit 1
fi

echo "Current version is $version"

# Increment version
# Split the version number into major and minor parts
major=$(echo "$version" | cut -d. -f1)
minor=$(echo "$version" | cut -d. -f2)

# Increment the minor part
new_minor=$((minor + 1))

# Construct the new version
new_version="$major.$new_minor"

echo "New version is $new_version"

# Replace the version in PKGBUILD
sed -i "s/pkgver=$version/pkgver=$new_version/" arch-packages/client/PKGBUILD
                                                                                                                                 
                                                                                                                                                                                                                    
# Git commit, tag and push                                                                                                                                                                                        
git add arch-packages/client/PKGBUILD                                                                                                                                                                             
git commit -m "Version bump to $new_version"                                                                                                                                                                      
git tag v$new_version                                                                                                                                                                                             
git push origin v$new_version