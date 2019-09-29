A mustardy EXTM3U proxy!

The M3U URL for your bouquet maker/editor
should now be:

    http://127.0.0.1:<PORT>/?url=<ORIGINAL M3U URL>

where \<PORT\> comes from the settings, the default
being 7290;

Required parameters:
- url=\<ORIGINAL M3U URL\> is whatever your provider
  told you to use, but needs to be URL encoded;
  just use any online encoder that works;
  this parameter can be repeated if you want to
  concatenate various M3Us.

Optional parameters:
- marker=\<MARKER\> indicates that the provided
  string should be used to mark catchup services;
  the default is not to mark them;
  this parameter will also require encoding;
- prefix=\<SOMETHING\> indicates we want to use
  \<MARKER\> as a prefix to the channel name, instead
  of the default which is to use it as a suffix;
- clean=\<SOMETHING\> indicates we want to cleanup
  the M3U data from possible UTF8 (or other) errors;
- vapi=\<SOMETHING\> forces use of VAPI. NOTE WELL:
  if you don't know what you're doing with this
  parameter, don't touch it, as your XC provider
  credentials may be leaked to the hardcoded VAPI
  provider.

Example of a typical XC API URL that would prefix
a marker of '[+] ':

http://<span></span>127.0.0.1:7290/?marker=<b>%5B%2B%5D%20</b>&prefix=1&url=<b>http%3A%2F%2FHOST%3APORT%2Fget.php%3Fusername%3DUSERNAME%26password%3DPASSWORD%26type%3Dm3u_plus</b>

Notice how only the "marker" and "url" parameter
values (in bold) should be encoded, the remainder
of the new/proxied URL should not.

Dev/Testing on OpenATV 6.2 and OpenPLi 6.2,
            Caveat Emptor.
