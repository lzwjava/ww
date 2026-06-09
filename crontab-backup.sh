PATH=/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin
*/10 * * * * /opt/homebrew/bin/ww appearance smart-auto >/dev/null 2>&1
0 * * * * /opt/homebrew/bin/ww projects update >/dev/null 2>&1
