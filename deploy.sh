#!/bin/bash

# Read current version                                                                                                                                                                                            
version=$(sed -nE 's/pkgver=([0-9]+)/\1/p' arch-packages/client/PKGBUILD)                                                                                                                                         
                                                                                                                                                                                                                    
# Increment version                                                                                                                                                                                               
new_version=$((version + 1))                                                                                                                                                                                      
                                                                                                                                                                                                                    
# Replace the version in PKGBUILD                                                                                                                                                                                 
sed -i "s/pkgver=$version/pkgver=$new_version/" arch-packages/client/PKGBUILD                                                                                                                                     
                                                                                                                                                                                                                    
# Git commit, tag and push                                                                                                                                                                                        
git add arch-packages/client/PKGBUILD                                                                                                                                                                             
git commit -m "Version bump to $new_version"                                                                                                                                                                      
git tag v$new_version                                                                                                                                                                                             
git push origin v$new_version