# Domoticz plugin for adding IHC via IHCServer as hardware.

IHC is a system to control all electricity in a house. See the IHCServer project for more explanations.

This plugin is glueing together the Domotics project (found here: https://github.com/domoticz/domoticz) and the IHCServer project (the original of which can be found here: https://github.com/skumlos/ihcserver, and including the glue to this plugin, it can be found here: https://github.com/kjlisby/ihcserver.git).

Please see the two projects regarding preconditions and installation.

I have been putting a few more words (in Danish) on my home automation projects and the IHC system in general here: https://lisby.dk/wordpress/?page_id=1061 and here: https://lisby.dk/wordpress/?p=3259

# Hardware needs

You will basically need:
- An IHC system
- A raspberry Pi
- An RS.485 interface

The Raspberry Pi might be of any model. But why not buy the latest and greatest model? It is not very expensive anyway. And it will have the power to run a lot of other plugins.

The RS.485 interface can also be bought for very little money: https://www.reichelt.de/raspberry-pi-usb-rs485-interface-rpi-usb-rs485-p242783.html Or you may buy an RS.485 USB dongle even cheaper from Ebay or from a Chinese shop.

The RS.485 interface must be connected to the RS.485 port (screw terminals) on the IHC controller via a twisted pair of wires.

Note that there is an RS.485 port on all generations of IHC controllers. I have however only experience with the very first controller generation, where there is an RS.232 connector on the front. 

NOTE THAT RS.232 AND RS.485 ARE TWO VERY DIFFERENT THINGS. The RS.232 connector on the IHC controller can only be used to program / set up the controller. I am using another dongle on the same Raspberry Pi (an RS.232 USB) to make this kind of changes in the controller utilizing the picocom terminal emulator.

# Installation of the plugin

The plugin can be installed basically any way you want. The important thing is that the plugin.py file can be found in a directory under the domoticz/plugins directory.

The easiest way is probably:
```shell
  $ cd domoticz/plugins
  $ git clone https://github.com/kjlisby/domoticz-ihc-plugin.git
  $ sudo systemctl restart domoticz
```

That way of installing also means that the plugin can always be updated this way:
```shell
  $ cd domoticz/plugins
  $ git pull
  $ sudo systemctl restart domoticz
```

# Plugin configuration

Use the Domoticz WEB UI to do the following:

- Go to Settings -> Hardware.
- Select Type as "IHC via IHCServer".
- Write any name you want for your connection to IHCServer.
- Write the IP address and port number of the HTTP server built into your IHCServer.
- Push the "Add" button.

The plugin will create and maintain a Domoticz light switch for each IHC input and output in IHCServer. The ID of each switch will be something like O-2-7, where O means output (or I for input), 2 is the IHC module number and 7 is the port on the IHC module.

The name of the Domoticz switch will be the same as set in IHCServer. Changes in IHCServer will have effect in Domoticz within 30 minutes.

# NOTE:

This plugin builds upon the WEBSocket abilities in Domoticz and especially a fix for issue #3398, which at present (JULY 2019) is only available in the beta release of Domoticz.
