# Ritalin.

THIS MIGHT/WILL AGE YOUR DECODER FLASH PREMATURELY, DO NOT USE!!!

Save the current service as the last service, and dump settings to flash.

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

This plugin is EXPERIMENTAL; it has been successfully tested on:
* Zgemma H7C - OpenATV 6.2.

THIS MIGHT/WILL AGE YOUR DECODER FLASH PREMATURELY, DO NOT USE!!!

## Description

This plugin runs in the background, subscribed to service events, and when it
detects an evStart (once you zap into a service) it will, if enabled in the
settings, save said service as the last service, and force a configuration file
write to flash.

## Settings

**"Enable"**
* "Enable or disable."
* Default: True.
* If disabled, the plugin won't try to save the servicce. Useful when checking
  the plugin behavior in association with the debug setting, or if you want to
  prevent premature flash aging (might as well uninstall the plugin, though).

**"Debug"**
* "Activate debug log."
* Default: False.
* If set to True, debug information is recorded under the
  /tmp/ritalin-debug.log file.

