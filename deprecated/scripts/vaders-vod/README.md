* Create VOD bouquet

NOTE: you probably want to take a peek at the Absolut
plugin, these days (although at the time of this
writing it doesn't support TV series).

Bring up bouquet list, then menu, then add bouquet: make sure to call it "vod" (no quotes).

* Make sure of the new bouquet file name

Should be called /etc/enigma2/userbouquet.vod__tv_.tv, if not, edit the script to reflect the proper name.

* Edit script with your username/pass

Make sure you keep the single-quotes (or use double-quotes instead) when assigning to the respective variables.

* Make script executable

chmod +x vaders-vod.py

* Create /etc/enigma2/bouquets directory

mkdir -p /etc/enigma2/bouquets

* Run script

./vaders-vod.py

* Check VOD menu and sub-menus, I hope you enjoy it...

If you start watching, it gets hard to exit, I generally escape to my first non-VOD channel by pressing the "1" key.

* Thanks to @SomeKewlName for testing!
