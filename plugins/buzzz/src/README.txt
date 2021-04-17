The Hive EXTM3U generator!

The M3U URL for your bouquet maker/editor
should be

    http://127.0.0.1:<port>/

where the <port> parameter comes from the
settings. By default, the port is 9090, so
the URL would be

    http://127.0.0.1:9090/

Remember that, unless static mode is
selected, the M3U needs to be refreshed
no later than every X (tbd) hours, or else
the credentials in it will expire.

Also, beware that forcing refreshes too
often might trigger a temporary block from
the server side, so try not to do it more
often than once an hour.

Dev/Testing on OpenATV 6.2 and OpenPLi 6.2,
            Caveat Emptor.
