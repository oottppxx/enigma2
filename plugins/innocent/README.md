Smooth EXTM3U generator!

The M3U URL for your bouquet maker/editor
should be

    http://127.0.0.1:<port>/

where the <port> parameter comes from the
settings. By default, the port is 8888, so
the URL would be

    http://127.0.0.1:8888/

Remember that the M3U needs to be refreshed
no later than every 4 hours, or else the
credentials in it will expire.

Also, beware that forcing refreshes too
often might trigger a temporary block from
the server side, so try not to do it more
often than once an hour.

For Suls, make sure the bouquets will be
generated as HLS/M3U8 (IPTV type 4097,
eventually 5002 or even 5001 if you installed
serviceapp). It won't hurt to install
my Suls (e2m3u2bouquet) mod, either.

For EPG, make sure, for now, that you
install my EPGImporter (xmlimport) mod,
otherwise you may find the EPG a little
sparse.


Big thanks to @duoduo80 for all the
testing and experimenting endured!!!


Dev/Testing on OpenATV 6.2, Caveat Emptor.
