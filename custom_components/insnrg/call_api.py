from aiohttp import ClientSession
from .exceptions import InsnrgPoolError
import logging

_LOGGER = logging.getLogger(__name__)
LOGIN_URL = "https://4rsb9rvte4.execute-api.us-east-2.amazonaws.com/prod/api/login"
CMD_URL = "https://4rsb9rvte4.execute-api.us-east-2.amazonaws.com/prod/api/cmd"


class InsnrgPool:
    """Main Interface to the Insnrg Pool Device"""

    def __init__(self, session: ClientSession, userName, password):
        self._url_login = LOGIN_URL
        self._userName = userName
        self._password = password
        self._session = session
        self._id_token = None
        self._user_id = None
        self._device_serial = None

    async def async_login(self):
        """Login to the system and store the token and user ID."""
        LOGIN_DATA = {
            "userName": self._userName,
            "password": self._password,
        }
        _LOGGER.debug("API: Attempting login.")
        resp = await self._session.post(self._url_login, json=LOGIN_DATA)

        try:
            data = await resp.json(content_type=None)
            _LOGGER.debug(f"API: Login response status: {resp.status}, data: {data}")
        except Exception:
            text_data = await resp.text()
            _LOGGER.debug(f"API: Login response status: {resp.status}, non-json data: {text_data}")
            data = {}

        if resp.status == 200 and data.get("auth", {}).get("idToken"):
            self._id_token = data["auth"]["idToken"]
            self._user_id = data.get("user", {}).get("userId")
            if data.get("devices"):
                self._device_serial = data["devices"][0]["serial"]
            else:
                self._device_serial = "DEMO"
            return True
        
        _LOGGER.error("API: Login failed.")
        return False

    async def test_insnrg_pool_credentials(self):
        """Function tests the credentials against the Insnrg Pool Servers"""
        return await self.async_login()

    async def _api_request(self, body):
        """Make a request to the command API."""
        if not self._id_token or not self._user_id:
            _LOGGER.debug("No token or user ID, attempting to log in.")
            if not await self.async_login():
                raise InsnrgPoolError(401, "Authentication failed.")

        head = {"Authorization": f"Bearer {self._id_token}"}
        
        body["userId"] = self._user_id

        _LOGGER.debug(f"API: Sending command with body: {body}")
        resp = await self._session.post(CMD_URL, headers=head, json=body)

        try:
            resp_data = await resp.json(content_type=None)
            _LOGGER.debug(f"API: Command response status: {resp.status}, data: {resp_data}")
        except Exception:
            resp_text = await resp.text()
            _LOGGER.debug(f"API: Command response status: {resp.status}, non-json data: {resp_text}")

        # If token has expired, try to re-login once
        if resp.status == 401:
            _LOGGER.debug("Token expired, attempting to re-login.")
            if await self.async_login():
                head = {"Authorization": f"Bearer {self._id_token}"}
                resp = await self._session.post(CMD_URL, headers=head, json=body)
            else:
                raise InsnrgPoolError(401, "Authentication failed after token refresh.")

        return resp

    async def get_insnrg_pool_data(self):
        """Function gets all the data for this user account from the Insnrg Pool api"""
        body = {"cmd": "getall"}
        resp = await self._api_request(body)

        result_dict = {}
        if resp.status == 200:
            discoverData = await resp.json(content_type=None)
            # The original debug log here is fine, no need to change it.

            for item in discoverData:
                device_id = item["deviceId"]
                status = item["properties"]
                result_dict[device_id] = {
                    "name": item["name"],
                    "deviceId": item["deviceId"],
                    "type": item["type"][0],
                    "switchStatus": next(
                        (
                            prop["value"]
                            for prop in status
                            if prop["namespace"] == "Alexa.PowerController"
                        ),
                        "",
                    ),
                    "toggleStatus": next(
                        (
                            prop["value"]
                            for prop in status
                            if prop["namespace"] == "Alexa.ToggleController"
                        ),
                        "",
                    ),
                    "thermostatStatus": next(
                        (
                            prop["value"]
                            for prop in status
                            if prop["namespace"] == "Alexa.ThermostatController"
                        ),
                        {},
                    ),
                    "temperatureSensorStatus": next(
                        (
                            prop["value"]
                            for prop in status
                            if prop["namespace"] == "Alexa.TemperatureSensor"
                        ),
                        {},
                    ),
                    "modeValue": next(
                        (
                            prop["value"]
                            for prop in status
                            if prop["namespace"] == "Alexa.ModeController"
                        ),
                        "",
                    ),
                }
                if item["type"][0] == "LIGHT":
                    result_dict["LIGHT_MODE"] = {
                        "name": "Light Modes",
                        "deviceId": "LIGHT_MODE",
                        "supportCmd": item["deviceId"],
                        "modeValue": next(
                            (
                                prop["value"]
                                for prop in status
                                if prop["namespace"] == "Alexa.ModeController"
                            ),
                            "",
                        ),
                        "modeList": item["options"],
                    }
                if "options" in item:
                    result_dict[device_id]["modeList"] = item["options"]
            results = result_dict
            _LOGGER.debug(f"Parsed result_dict: {results}")
        else:
            raise InsnrgPoolError(resp.status, "Server error.")
        return results

    async def _send_command(self, body):
        """Send a command and return True on success."""
        try:
            set_state_resp = await self._api_request(body)
            if set_state_resp.status == 200:
                return True
            else:
                _LOGGER.error(f"Failed to send command: {body.get('cmd') or body.get('cmdType')}. Status: {set_state_resp.status}")
                return False
        except InsnrgPoolError as e:
            _LOGGER.error(f"Error sending command: {body.get('cmd') or body.get('cmdType')}. Error: {e}")
            return False
        except Exception as e:
            _LOGGER.error(f"An unexpected error occurred sending command: {e}")
            return False

    async def turn_the_switch(self, mode, deviceId):
        mode_to_cmdType = {"ON": "TurnOn", "OFF": "TurnOff", "TIMER": "TimerOn"}
        body = {
            "cmd": "setDeviceStatus",
            "cmdType": mode_to_cmdType[mode],
            "deviceId": deviceId,
        }
        return await self._send_command(body)

    async def set_thermostat_temp(self, temp_value, deviceId):
        body = {
            "cmd": "setTemperature",
            "tempValue": temp_value,
            "deviceId": deviceId,
        }
        return await self._send_command(body)

    async def set_chemistry(self, chem_value, deviceId):
        body = {
            "cmd": "setChemistry",
            "chemValue": chem_value,
            "deviceId": deviceId,
        }
        return await self._send_command(body)

    async def change_light_mode(self, mode, deviceId):
        body = {
            "cmd": "setLightMode",
            "lightValue": mode,
            "deviceId": deviceId,
        }
        return await self._send_command(body)
