@echo off
cd /d e:\Python\PROJECT\website
git add -A
git commit -m "fix: resolve image paths to curated static paths in seed sync"
git push
git log -1 --oneline
echo DONE