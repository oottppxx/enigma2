Enigma2 Snif.

Tries to detect (sniff) streaming connections to the box,
extract the Basic authentication digest (namely the user),
and track per user limits as configured.

Connections exceeding the limits will be tentatively reset.

There are, of course, obvious ways to circumvent the detection,
but they're probably out of reach for most users.

Note: currently the plugin only handles streams over IPv4, and
it was only tested on OpenATV 6.2.

@oottppxx
