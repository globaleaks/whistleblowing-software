import tornado.web
import tornado.ioloop

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('hello world!')

class InfoHandler(tornado.web.RequestHandler):
    """
    Return a JSONObject containing all informations about the node.
    """

    def get(self):
        """
        Fetch the node information from the core in json form, then return it.
        """
        self.write('not implemented')

    def post(self):
        raise tornado.web.HTTPError(501)

    def delete(self):
        raise tornado.web.HTTPError(501)


class TipHandler(tornado.web.RequestHandler):
    """
    If a specific submission is requested, return its content (GET)
    If a new submission is created, append it (POST)
    If some material is attached to a submission, map it (PUT)
    If a submission shall be removed, drop it from the database (DELETE)
    """
    def get(self, submission_id):
        pass

class TipStatisticsHandler(tornado.web.RequestHandler):
    """
    Retrive informations about a particular submission.
    """
    def get(self, submission_id):
        pass


class TipCommentsHandler(tornado.web.RequestHandler):
    """
    Retrive comments for a specific submission.
    """

    def get(self, submission_id, comment_id):
        print submission_id, comment_id
        # raise NotImplementedError

class TipMaterialHandler(tornado.web.RequestHandler):
    """
    """



application = tornado.web.Application([
    (r"^/$", IndexHandler),
    (r"^/info/$", InfoHandler),
    (r"^/tip/([\d\w]{5})/$", TipHandler),
    (r"^/tip/([\d\w]{5})/statistics$", TipHandler),
    # fuck shit this regexp doesnt work XXX
    (r"^/tip/([\d\w]{5})/comments/(\?([^#][\d\w]+))$", TipCommentsHandler),

])


if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
