# to find your username.
import logging

import pyspeedtest


def speed_test():
    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
    st = pyspeedtest.SpeedTest(host="speedtest.copel.net")
    down = st.download()
    up = st.upload()
    ping = st.ping()
    sDonload = pyspeedtest.pretty_speed(down)

    logging.debug("Download speed: %s", sDonload)
    return down, up, ping
