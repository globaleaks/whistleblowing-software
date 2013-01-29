
class MacroOperation():

    from globaleaks import main

    transactor = main.transactor

    def getStore(self):

        from globaleaks.config import config
        return config.main.zstorm.get('main_store')

    # TODO think to add "returnInfo" and collect logs
    # after, the handler, would call the other store thread

    def returnData(self, data):

        if type(data) == type([]):
            self._data = list(data)
        elif type(data) == type({}):
            self._data = dict(data)
        else:
            raise NotImplementedError

    def returnCode(self, http_code):

        self._http = http_code

    def returnValues(self):

        returnDict = { 'data' : self._data,
                       'code' : self._http }

        return dict(returnDict)


class LogOperation():
    pass
