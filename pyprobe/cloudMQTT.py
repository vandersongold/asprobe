#!/usr/bin/env python
import logging

from cloudServer import CloudServer
import paho.mqtt.client as mqtt

from helper.filter import FilterTopic
from settings_local import MQTT_HOST, MQTT_PORT

KEEP_ALIVE_SEC = 3600  # One minute

class CloudMQTT(object):
    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

        self._service_host = MQTT_HOST
        self._service_port = MQTT_PORT
        # Initialize event callbacks to be None so they don't fire.
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        # Initialize MQTT client.
        self._client = mqtt.Client("", True, None, mqtt.MQTTv31)
        # self._client.username_pw_set(username, key)
        self._client.on_connect    = self._mqtt_connect
        self._client.on_disconnect = self._mqtt_disconnect
        self._client.on_message    = self._mqtt_message
        self._connected = False

    def _mqtt_connect(self, client, userdata, flags, rc):
        logging.debug('Client on_connect called.')
        # Check if the result code is success (0) or some error (non-zero) and
        # raise an exception if failed.
        if rc == 0:
            self._connected = True
        else:
            # 0: Connection successful 1: Connection refused - incorrect protocol version 2: Connection refused - invalid client identifier 3: Connection refused - server unavailable 4: Connection refused - bad username or password 5: Connection refused - not authorised 6-255: Currently unused.
            raise RuntimeError('Error connecting to Mqtt  IO with rc: {0}'.format(rc))
        # Call the on_connect callback if available.
        if self.on_connect is not None:
            self.on_connect(self)

    def _mqtt_disconnect(self, client, userdata, rc):
        logging.debug('Client on_disconnect called.')
        self._connected = False
        # If this was an unexpected disconnect (non-zero result code) then just
        # log the RC as an error.  Continue on to call any disconnect handler
        # so clients can potentially recover gracefully.
        if rc != 0:
            logging.debug('Unexpected disconnect with rc: {0}'.format(rc))
        # Call the on_disconnect callback if available.
        if self.on_disconnect is not None:
            self.on_disconnect(self)

    def _mqtt_message(self, client, userdata, msg):
        logging.debug('Client on_message called. %s', msg.topic)
        # self.on_message(self, userdata, msg)
        # Parse out the feed id and call on_message callback.
        # Assumes topic looks like "username/feeds/id"
        try:
            parsed_topic = msg.topic.split('/')
        except ValueError:
            logging.error("no expected topic type")

        if self.on_message is not None:
            filter = parsed_topic[2]
            objtFil = FilterTopic()
            id = objtFil.convert(filter=filter)
            if (id != FilterTopic.INVALID):
                payload = '' if msg.payload is None else msg.payload.decode('utf-8')
                self.on_message(self, id, payload)

    def connect(self, **kwargs):
        # Skip calling connect if already connected.
        if self._connected:
            return
        self._client.connect(self._service_host, port=self._service_port,
            keepalive=KEEP_ALIVE_SEC, **kwargs)

    def subscribe_main_channels(self, deviceId):
        topic_list = [
            "probe/" + deviceId + "/speedtest/exec",
            "probe/" + deviceId + "/reset",
            "probe/" + deviceId + "/command",
            "probe/" + deviceId + "/apply",
            "probe/" + deviceId + "/latency/exec",
            "probe/" + deviceId + "/latency/status",
            "probe/" + deviceId + "/status/req"
        ]

        for topic in topic_list:
            logging.debug('MQTT Subscribe topic: %s', topic)
            self._client.subscribe(topic)

    def disconnect(self):
        """Disconnect MQTT client if connected."""
        if self._connected:
            self._client.disconnect()

    def loop_background(self):
        self._client.loop_start()

    def publish(self, topic, message):
        self._client.publish(topic, message)

    def publish_status(self, deviceId):
        topic = "probe/" + deviceId + "/status/"
        self._client.publish(topic, '1')

    def publish_command_result(self, message):
        app = CloudServer.Instance()
        probe = app.get_probe()
        topic_command = "probe/" + probe.objectId + "/command/result"
        self._client.publish(topic_command, message)

    def publish_speedtest_result(self, message):
        app = CloudServer.Instance()
        probe = app.get_probe()
        topic_command = "probe/" + probe.objectId + "/speedtest/result"
        self._client.publish(topic_command, message)