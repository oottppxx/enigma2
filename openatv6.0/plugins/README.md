* Heinz is a "ketchup" plugin, supporting both Vaders API as well as Xtream-Codes API.

* Balancer is a server switcher for Vaders (and resellers).

**NOTE:** the Balancer plugin can leak your credentials in a multi-provider setup, if not
invoked from a Vaders' stream. Heinz avoids this by using the vFilter and xFilter settings,
make sure to use/edit those (separate multiple matches in each filter with "!").

Thanks to the folks in PMC:Enigma (namely @falleen, @BillHicks, @Bill) and DeathStar (namely @agentsmith1, @SomeKewlName).

Although dev/tested in Open ATV 6.0, these plugins were reported to also work in:

Open ATV 6.2 (@corkman, @falleen)

OpenViX 5.1.x (@SomeKewlName)

WooshBuild 7 / OpenATV 6.1 (@BillHicks)
