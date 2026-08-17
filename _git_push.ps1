Set-Location e:\Python\PROJECT\website
git add -A 2>&1 | Out-File -FilePath _git_log.txt -Encoding utf8
git commit -m "fix: resolve image paths to curated static paths in seed sync" 2>&1 | Out-File -FilePath _git_log.txt -Append -Encoding utf8
git push 2>&1 | Out-File -FilePath _git_log.txt -Append -Encoding utf8
git log -1 --oneline 2>&1 | Out-File -FilePath _git_log.txt -Append -Encoding utf8