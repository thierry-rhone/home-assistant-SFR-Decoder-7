# Custom component
This is a custom component to allow control of SFR TV decoder 7 in HomeAssistant. 

This project is a fork of dragouf/SFRTV I use  the remote.py file from this project.

# Manual installation



Install it as you would do with any homeassistant custom component:

1. Download `custom_components` folder.
1. Copy the `sfrtv` directory within the `custom_components` directory of your homeassistant installation. The `custom_components` directory resides within your homeassistant configuration directory.
**Note**: if the custom_components directory does not exist, you need to create it.
After a correct installation, your configuration directory should look like the following.
    ```
    └── ...
    └── configuration.yaml
    └── custom_components
        └── sfrtv
            └── __init__.py
            └── exceptions.py
            └── manifest.json
            └── media_player.py
            └── remote.py
            └── sources.json
   ```

# Configuration

Once the component has been installed, you need to configure it in order to make it work.

- Edit the `configuration.yaml` file
```

media_player:
 - platform: sfrtv
   name: decodeur SFR
   host: <YOUR DECODER IP ADDRES>
```
# Sources
As the websocket interface of the decoder does not allow to obtain the list of channels, I created a source.json file in the sfrtv folder.
You can modify it with your own channels (which depends on your subscription).

It is important to respect the exact name returned by the decoder (upper case, lower case)
Warning: For the display of the channel on the decoder everything is converted to uppercase

# limitation

Due to a bug on the websocket of the decoder, it appears `power off` when you go to the lower menus: Jeux replay enregistrements...

--------------------------------------------------------------
--------------------------------------------------------------

# sfrtvctl (original works of dragouf)

python library which can also be use in command line.

Summary
==========

commands are sent by websocket on port 7682 with sub-protocol lws-bidirectional-protocol.

there is multiple kind of data structure depending on kind of commands we went to send.

send commands :
BUTTONEVENT structure for  classical remote keys (volume, power, ok, return, pause, play, forward, rewind, directionnal keys, num pad)
ZAP structure to send a channel number in 1 request.
APP structure to launch special function of the decoder (mosaic, tv guide, vod, replay, recording, media center, settings)
SETVOLUME structure to set the volume
KEYBOARD structure to type when inside input field

Info commands (not yet implemented):
GETINFO and GETVERSION

Installation
============

sfrtvctl can be installed using `pip <(https://pip.pypa.io/>`_:

::

    # pip install websocket-client
    # pip install sfrtvctl

Alternatively you can clone the Git repository and run:

::

    # python setup.py install

It's possible to use the command line tool without installation:

::

    $ python -m sfrtvctl

BUTTONEVENT
============

BUTTONEVENT take a second argument to specify the key pressed and a third in case you specify NUM.

the table here resume each possible actions for BUTTONEVENT :

| Key Pressed (second argument)  | Description                                      |
| ------------------------------ | -------------------------                        |
| VUP                            | Volume up                                        |
| VDOWN                          | Volume Down                                      |
| RIGHT                          | multidirectionnal right                          |
| LEFT                           | multidirectionnal left                           |
| UP                             | multidirectionnal up                             |
| DOWN                           | multidirectionnal down                           |
| PUP                            | Program up                                       |
| PDOWN                          | Program down                                     |
| INFO                           | Current program info                             |
| RETURN                         | return key                                       |
| OK                             | OK key                                           |
| NUMBER                         | a digit key. take a third argument for the digit |
| PLAYPAUSE                      | play or pause key                                |
| FORWARD                        | fast forward key                                 |
| REWIND                         | fast rewind  key                                 |
| MUTE                           | mute sound key                                   |
| POWER                          | power on/off key                                 |

in command line mode here is an example of command :  
```sfrtvctl --host 192.168.1.100  BUTTONEVENT VUP``` # increase volume  
```sfrtvctl --host 192.168.1.100  BUTTONEVENT NUMBER 1``` # type 1 on num pad (will change channel if watching tv)  

ZAP
====

ZAP command is simple, it just take a number as second argument.

in command line mode here is an example of command :  
```sfrtvctl --host 192.168.1.100  ZAP 180``` # will go to channel 180  

APP
===

| Command       | Description                       |
| ------------- | --------------------------------- |
| MOSAIC        | Mosaique                          |
| TVGUIDE       | Guide TV                          |
| VOD           | SFR Play                          |
| REPLAY        | TV replay                         |
| RECORDING     | List recorded shows               |
| MEDIACENTER   | media center (usb, network media) |
| SETTINGS      | Decoder settings                  |

in command line mode here is an example of command :
```sfrtvctl --host 192.168.1.100  MOSAIC``` # will display mosaique

SETVOLUME
==========

SETVOLUME command is simple, it just take a number between 1 and 100 as second argument to set volume.

in command line mode here is an example of command :  
```sfrtvctl --host 192.168.1.100  SETVOLUME 40``` # will set volume to 40  

KEYBOARD
=========

will send keyboard data. This command has a special character to start search which you can send by passing SEARCH as a second argument. To start typing you must send first VALUE and then a third argument.

| Command       | Description                              |
| ------------- | ---------------------------------------- |
| SEARCH        | Start search                             |
| VALUE         | send keyboard key pass in third argument |


in command line mode here is an example of command :  
```sfrtvctl --host 192.168.1.100  SEARCH``` # will start search  
```sfrtvctl --host 192.168.1.100  VALUE a``` # will type a in an input field  


Library usage
=============

sfrtvctl can be imported as a Python 3 library:

.. code-block:: python

    import sfrtvctl

A context managed remote controller object of class ``Remote`` can be
constructed using the ``with`` statement:

.. code-block:: python

    with sfrtvctl.Remote(config) as remote:
        # Use the remote object

The constructor takes a configuration dictionary as a parameter. All
configuration items must be specified.

| Key     | Type   | Description                                 |
|---------|--------|---------------------------------------------|
| host    | string | Hostname or IP address of the decoder.      |
| port    | int    | TCP port number. (Default: ``7682``)        |
| timeout | int    | Timeout in seconds. ``0`` means no timeout. |

The ``Remote`` object is very simple and you only need the ``control(key, arg1, arg2)``
method. See tables above for more details about commands you can pass. You can call ``control`` multiple times
using the same ``Remote`` object. The connection is automatically closed when
exiting the ``with`` statement.
