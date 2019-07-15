# Domoticz plugin for adding IHC via IHCServer as hardware.

IHC is a system to control all electricity in a house. See the IHCServer project for more explanations.

This plugin is glueing together the Domotics project (found here: https://github.com/domoticz/domoticz) and the IHCServer project (found here: https://github.com/skumlos/ihcserver).

Please see the two projects regarding preconditions and installation.

# Installation of the plugin

The plugin can be installed basically any way you want. The important thing is that the plugin.py file can be found in a directory under the domoticz/plugins directory.

The easiest way is probably:
```shell
  $ cd domoticz/plugins
  $ git clone https://github.com/domoticz/domoticz.git
  $ sudo systemctl restart domoticz
```

That way of installing also means that the plugin can always be updated this way:
```shell
  $ cd domoticz/plugins
  $ git pull
  $ sudo systemctl restart domoticz
```

The plugin will create and maintain a Domoticz light switch for each IHC input and output in IHCServer. The ID of each switch will be something like O-2-7, where O means output (or I for input), 2 is the IHC module number and 7 is the port on the IHC module.

The name of the Domoticz switch will be the same as set in IHCServer. Changes in IHCServer will have effect in Domoticz within 30 minutes.

# Plugin configuration

Use the Domoticz WEB UI to do the following:

- Go to Settings -> Hardware.
- Select Type as "IHC via IHCServer".
- Write any name you want for your connection to IHCServer.
- Write the IP address and port number of the HTTP server built into your IHCServer.
- Push the "Add" button.

# NOTE:

This plugin builds upon the WEBSocket abilities in Domoticz and especially a fix for issue #3398, which at present (JULY 2019) is only available in the beta release of Domoticz.
