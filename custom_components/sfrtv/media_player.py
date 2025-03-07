"""
Support for interface with a SFR TV (STB7).

"""
import logging
import socket
import json
import voluptuous as vol
import aiofiles as aiof
import time
from . import exceptions
from datetime import timedelta
from . remote import Remote
from homeassistant.util import dt as dt_util
try:
    from homeassistant.components.media_player import MediaPlayerEntity, PLATFORM_SCHEMA
except ImportError:
    from homeassistant.components.media_player import MediaPlayerDevice as MediaPlayerEntity, PLATFORM_SCHEMA

from homeassistant.components.media_player.const import (
    MEDIA_TYPE_CHANNEL,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_TURN_OFF,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_STEP,
    SUPPORT_STOP,
    SUPPORT_SEEK,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_PLAY,
    SUPPORT_TURN_ON
    )
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
    STATE_PAUSED,
    STATE_PLAYING,
    )
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_TIMEOUT = 'timeout'

DEFAULT_NAME = 'SFR TV Remote'
DEFAULT_PORT = 7682
DEFAULT_TIMEOUT = 20

KNOWN_DEVICES_KEY = 'STB7_known_devices'

ATTR_MEDIA_DESCRIPTION = "media_description"
ATTR_MEDIA_END_TIME = "media_end_time"
ATTR_MEDIA_START_TIME = "media_start_time"

SUPPORT_SFRTV = (
    SUPPORT_PAUSE
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
    | SUPPORT_SEEK
    | SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_STOP
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_PLAY
    | SUPPORT_VOLUME_STEP
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    }
)

# pylint: disable=unused-argument
async def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the SFR TV platform."""
    known_devices = hass.data.get(KNOWN_DEVICES_KEY)
    if known_devices is None:
        known_devices = set()
        hass.data[KNOWN_DEVICES_KEY] = known_devices

    if config.get(CONF_HOST) is not None:
        host = config.get(CONF_HOST)
        name = config.get(CONF_NAME)
        timeout = config.get(CONF_TIMEOUT)
    else:
        _LOGGER.warning("Cannot determine device")
        return

    port = DEFAULT_PORT
    config_path = hass.config.path("custom_components/sfrtv/sources.json")
    async with aiof.open(config_path, encoding="utf8") as sourcesfile:
        source_list = await sourcesfile.read()

    # Only add a device once
    # config.
    ip_addr = socket.gethostbyname(host)
    if ip_addr not in known_devices:
        known_devices.add(ip_addr)
        add_devices([SfrTVDevice(host, port, name, timeout, source_list)])
        _LOGGER.info("SFR TV (STB7) %s:%d added as '%s'", host, port, name)
    else:
        _LOGGER.info("Ignoring duplicate SFR TV %s:%d", host, port)

class SfrTVDevice(MediaPlayerEntity):
    """Representation of a SFR TV."""

    def __init__(self, host, port, name, timeout, source_list):
        """Initialize the SFR device."""
        # Save a reference to the imported classes
        self._exceptions_class = exceptions
        self._remote_class = Remote
        self._name = name
        self._current_source = None
        # Assume that the TV is not muted
        self._muted = False
        # Assume that the TV is in Play mode
        self._state = STATE_UNKNOWN
        self._remote = None
        # Mark the end of a shutdown command (need to wait 5 seconds before
        # sending the next command to avoid turning the TV back ON).
        self._end_of_power_off = None
        self._source = None
        self._source_list = json.loads(source_list)

        # Generate a configuration for the SFR library
        self._config = {
            'name': 'HomeAssistant',
            'description': name,
            'id': 'ha.component.sfrtv',
            'port': port,
            'host': host,
            'timeout': timeout,
            'source_list': source_list,
        }

    def update(self):
        """Retrieve the latest data."""
        # get session status
        self.send_key('GETINFO', '', '')

    def get_remote(self):
        """Create or return a remote control instance."""
        if self._remote is None:
            # We need to create a new instance to reconnect.
            self._remote = self._remote_class(self._config)
        return self._remote

    def send_key(self, key, keyarg1, keyarg2):
        """Send a key to the tv and handles exceptions."""
        _LOGGER.debug("Sending command: %s %s %s", key, keyarg1, keyarg2)
        if self._power_off_in_progress() and not (key == 'GETINFO') and not (keyarg1 == 'POWER'):
            _LOGGER.info("TV is powering off, not sending command: %s  ", key)
            return
        try:
          self.get_remote().control(key, keyarg1, keyarg2 )
        except (self._exceptions_class.UnhandledResponse,
                self._exceptions_class.AccessDenied, BrokenPipeError):
            # We got a response so it's on.
            # BrokenPipe can occur when the commands is sent to fast
            self._state = STATE_ON
            self._remote = None
            return
        except (self._exceptions_class.ConnectionClosed, OSError):
            self._state = STATE_OFF
            self._remote = None
        if self._power_off_in_progress():
            self._state = STATE_OFF

        time.sleep(0.2)
        resp_dict = self.get_remote().read_response ()
        if resp_dict.get ('Action') == "GetSessionsStatus":
            if resp_dict.get ('RemoteResponseCode') == "OK":
                self._source = resp_dict['Data']['LiveSession']['LiveItem']['CurrentChannel']['Name']
                if resp_dict['Data']['LiveSession']['Speed'] == 1 :
                    self._state = STATE_PLAYING
                else:
                    self._state = STATE_PAUSED
            else:
                self._state = STATE_OFF

    def _power_off_in_progress(self):
        return self._end_of_power_off is not None and \
               self._end_of_power_off > dt_util.utcnow()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def source(self):
        """Return the current input source."""
        return self._source

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_SFRTV

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        # return self._client.media_type
        return MEDIA_TYPE_CHANNEL

    @property
    def source_list(self):
        source_list = []
        source_list.extend(list(self._source_list))
        return source_list

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes.
        isRecording:        Is the box currently recording.
        currservice_fulldescription: Full program description.
        currservice_begin:  is in the format '21:00'.
        currservice_end:    is in the format '21:00'.
        """
        if self._state == STATE_OFF:
            return {}
        return {
            ATTR_MEDIA_DESCRIPTION: self._source
            }


    def turn_off(self):
        """Turn off media player."""
        _LOGGER.debug("turning off stb7")
        self._end_of_power_off = dt_util.utcnow() + timedelta(seconds=4)
        self.send_key('BUTTONEVENT', 'POWER', '')

    def turn_on(self):
        """Turn the media player on."""
        _LOGGER.debug("turning on stb7")
        self.send_key('BUTTONEVENT', 'POWER', '')
        time.sleep(2)
        self.send_key('BUTTONEVENT', 'OK', '')

    def volume_up(self):
        """Volume up the media player."""
        self.send_key('BUTTONEVENT', 'VUP', '')

    def volume_down(self):
        """Volume down media player."""
        self.send_key('BUTTONEVENT', 'VDOWN', '')

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        tv_volume = volume * 100
        self.send_key('SETVOLUME', tv_volume, '')

    def mute_volume(self, mute):
        """Send mute command."""
        self.send_key('BUTTONEVENT', 'MUTE', '')

    def media_play(self):
        """Send play command."""
        self.send_key('BUTTONEVENT', 'PLAYPAUSE', '')

    def media_pause(self):
        """Send media pause command to media player."""
        self.send_key('BUTTONEVENT', 'PLAYPAUSE', '')

    def media_stop(self):
        """Send media pause command to media player."""
        self.send_key('BUTTONEVENT', 'STOP', '')

    def media_next_track(self):
        """Send next track command."""
        self.send_key('BUTTONEVENT', 'FORWARD', '')

    def media_previous_track(self):
        """Send the previous track command."""
        self.send_key('BUTTONEVENT', 'REWIND', '')

    def select_source(self, source):
        """Select input source."""
        self._current_source = source
        if source in self._source_list:
            self.send_key('ZAP', self._source_list[source], '')
