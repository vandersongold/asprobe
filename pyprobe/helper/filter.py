class FilterTopic:
    INVALID = -1
    SPEED_TEST = 1
    REBOOT = 2
    COMMAND = 3
    APPLY = 4
    LATENCY = 5
    STATUS = 6

    def convert(self, filter):
        if (filter == "speedtest"):
            return  self.SPEED_TEST
        elif (filter == "reset"):
            return self.REBOOT
        elif (filter == "command"):
            return self.COMMAND
        elif (filter == "apply"):
            return self.APPLY
        elif (filter == "latency"):
            return self.LATENCY
        elif (filter == "status"):
            return self.STATUS
        else:
            return self.INVALID