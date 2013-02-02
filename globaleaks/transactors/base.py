
class MacroOperation():

    from globaleaks import main

    transactor = main.transactor

    def getStore(self):

        from globaleaks.config import config
        return config.main.zstorm.get('main_store')

    # TODO think to add "returnInfo" and collect logs
    # after, the handler, would call the other store thread

    def returnData(self, data):
        """
        Storm require copy of the return value, or the
        then the transact thread is closed, the stack
        would http://www.youtube.com/watch?v=C7JZ4F3zJdY fart.
        """

        if type(data) == type([]):
            self._data = list(data)
        elif type(data) == type({}):
            self._data = dict(data)
        else:
            raise NotImplementedError

    def returnCode(self, http_code):

        self._http = http_code

    def prepareRetVals(self):

        returnDict = { 'code' : self._http }

        if hasattr(self, '_data' ):
            returnDict.update({ 'data' : self._data })

        return dict(returnDict)


class LogOperation():
    pass
