PyShell.

Point your telnet client to:

    127.0.0.1 <port>

where the <port> parameter comes from the
settings. By default, the port is 8089.

### START OF EXAMPLE USAGE ###
```
# telnet localhost 8089
!h for help
>>> !h      
Commands:

!d ADDR2   displays the in-memory lines between [n1,n2[
!e         executes the in-memory lines
!r ADDR2   removes the in-memory lines between [n1,n2[
!m ADDR3   moves the in-memory lines between [n1,n2[ to line n3
!a FILE    appends the lines in FILE to the in-memory lines
!w FILE    writes the in-memory lines to FILE
!q         quits the session but keeps the in-memory lines
!x         exits the session and clears the in-memory lines
!h         displays this help message

Arguments:

FILE       expects a path to a file
ADDRn      are addresses, expected in the form: n1,n2,n3
ADDR2      uses n1 and n2; n3 is ignored if present.
ADDR3      uses all of n1, n2, and n3
If any of n1, n2, or n3 are ommitted, adequate defaults are assumed.


Any other input is appended to the in-memory lines, as is,
no validation is performed!

>>> !d
>>> from Screens.MessageBox import MessageBox
>>> session.open(MessageBox, 'Hello World!')
>>> !d
0:	from Screens.MessageBox import MessageBox
1:	session.open(MessageBox, 'Hello World!')
>>> !e
StdOut/StdErr:
[SKIN] processing screen MessageBoxSimple:
[SKIN] processing screen MessageBoxSimple_summary:
[SCREENNAME]  ['MessageBoxSimple_summary', 'SimpleSummary']
[SCREENNAME]  ['MessageBoxSimple']
Last Unhandled Exception:
None
```
### END OF EXAMPLE USAGE ###


Dev/Testing on OpenATV 6.2, Caveat Emptor.
