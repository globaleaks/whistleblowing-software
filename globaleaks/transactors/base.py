from twisted.internet.defer import returnValue

class MacroOperation():

    from globaleaks import main

    transactor = main.transactor

    def getStore(self):

        from globaleaks.config import config
        return config.main.zstorm.get('main_store')

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

        returnValue(dict(returnDict))


class LogOperation():
    pass
