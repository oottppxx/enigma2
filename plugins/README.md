* Heinz is a "ketchup" plugin, supporting both Vaders API as well as Xtream-Codes API.

* PLHeinz is the same as Heinz, but specific for OpenPLi, due to code base differences
  making it difficult (for me) to use SingleEPG builtin screens.

* Subway is a plugin to display subscription info, if the service supports it.

* MiracleWhip is a plugin to edit Suls/IPTVBouquetMaker/E2m3u2bouquet provider configs
  via the webbrowser.

* Balancer is a server switcher for Vaders (and resellers).

* McDonnells is a match center events lister/zapper for Vaders (and resellers), and
  also an events lister/zapper for Smooth Streams.

* PyShell is a plugin for developers/coders - it provides a very simple Python
  shell with access to the Enigma2 runtime environment, so small (or not so small)
  snippets of code can be tested and experimented with while avoiding crashes.

* Innocent is a local M3U proxy for SmoothStreams.

Most plugins, except for PLHeinz, were developed and tested on OpenATV. The version
numbers of the plugins generally track the major/minor release for the system where
they were developed and tested (e.g., Heinz up to 6.0.4u was developed and tested on an
OpenATV 6.0 system). For minor updates, the major/minor release tracking isn't expected
to change, even if the current system has evolved - let me know about innaccuracies.

PLHeinz is a different animal, and its version number tracks the closest Heinz release
it was based/updated from.

Typically, the README files for each plugin/script will provide the necessary information
regarding where they were developed/tested, so one can make an educated guess if they'd
work on a particular system. In the end, there's nothing like trying it out.

Original greetings regarding Heinz and Balancer below:

Thanks to the folks in PMC:Enigma (now extinct, namely @falleen, @BillHicks, @Bill) and DeathStar (namely @agentsmith1, @SomeKewlName).

Although dev/tested in Open ATV 6.0, these plugins were reported to also work in:

Open ATV 6.2 (@corkman, @falleen)

OpenViX 5.1.x (@SomeKewlName)

WooshBuild 7 / OpenATV 6.1 (@BillHicks)

For Balancer only: OpenPLi 6.2 (@DutchDude6X)
