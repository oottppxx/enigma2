# Buzzz

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

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

## Description

The Hive service doesn't provide an M3U URL, which is generally needed for
Enigma2 service bouquet generation. This plugin allows the users to specify the
plugin handler as the M3U URL, and when using a bouquet generator, the plugin
handler will be invoked and will fetch data from The Hive and translate it into
the required M3U format.

## Settings

**"Username"**
* "Username."
* Default: "".
* Your Hive username.

**"Password"**
* "Password."
* Default: "".
* Your Hive password.

**"Type"**
* "Stream type."
* Default: m3u8.
* The type of stream to request the provider to provide, either m3u8 or ts.

**"Port"**
* "EXTM3U URL port."
* Default: 9090
* The TCP/IP port the plugin will be listening on for M3U requests.

**"Refresh"**
* "Refresh time (hours)."
* Default: 4 hours.
* This controls how often to refresh the token if static mode is used.

**"Static"**
* "Static EXTM3U."
* Default: False.
* If set to True, all the services in the generated M3U will have
  localhost/127.0.0.1 as the service host and the plugin port as the service
  port in the URL, and the token will be the string BUZZZ. Whenever a new
  service is zapped to, the plugin handler will be invoked and it will redirect
  to the real service, with a fresh token (the token is refreshed every N hours,
  controlled by the "Refresh" setting). If static mode isn't used, then the M3U
  needs to be refreshed every N hours, or else at some point the service tokens
  will have expired and the streams won't work.

**"Debug"**
* "Activate debug log."
* Default: False.
* If set to True, debug information is recorded under /tmp/absolut-debug.log file.

