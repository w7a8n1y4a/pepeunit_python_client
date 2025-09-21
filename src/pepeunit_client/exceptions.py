class PepeunitClientError(Exception):
    def __init__(self, message):
        super().__init__("PepeunitClientError: {}".format(message))
