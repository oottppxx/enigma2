# Auto Off.

Stop current service when entering standby.

Optionally resumes it after exiting standby.

Also allows to run commands when entering and exiting standby.

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

## Description

Apparently some Enigma2 systems don't stop IPTV services once the box enters
standby. This plugin polls for when the box is in standby and stops the current
service, optionally also running a provided shell command. Similarly, the plugin
polls for when the box is no longer in standby and tries to resume the previous
service, optionally also running a provided shell command when this happens.

## Settings

**"Poll Interval (seconds)"**
* "Seconds between polls for power state (min. 5)."
* Default: 15 seconds.
* This controls how often to check if the box entered or left the standby state.

**"Stop Delay (seconds)"**
* "Delay before stopping the service after detecting standby state (max. poll interval - 5)."
* Default: 0 seconds.
* This controls how much to wait after detecting that the box entered standby
  before the service is stopped (by the plugin).

**"Resume Service"**
* "Resume service after standby exit detection."
* Default: True
* This controls if the plugin will attempt to resume the previous service once
  it detects that the box is now on.

**"Standby Command"**
* "Command to invoke after standby enter detection."
* Default: "".
* Here you can define a shell command or script to be invoked by the plugin once
  it detects that the box entered standby.

**"Resume Command"**
* "Command to invoke after standby exit detection."
* Default: ""
* Similar to the standby command, but for when the box is turned back on.

**"Resume Command On GUI (Re)Start"**
* "Also invoke the resume command when the GUI (Re)Starts."
* Default: False.
* If set to True, the resume command will also be invoked when the plugin
  starts, which will happen after a GUI/Enigma2 (re)start, including when the
  box boots.

**"Debug"**
* "Activate debug log."
* Default: False
* If set to True, debug information is recorded under the
  /tmp/autoff-debug.log file.
