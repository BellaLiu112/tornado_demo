import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpclient
import datetime
from tornado.options import define, options

define("port", default=8005, help="run on the given port", type=int)



class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch("http://www.qq.com", callback=self.on_response)

    def on_response(self, response):
        body = response.body
        result_count = len(body)
        now = datetime.datetime.utcnow()
        self.write("""
            <div style="text-align: center">
                <div style="font-size: 72px">%s</div>
                <div style="font-size: 144px">%s</div>
                <div style="font-size: 24px">%s</div>
                <div style="font-size: 24px">hhhh</div>
            </div>""" % ("d", result_count, now))
        return response;
        self.finish()


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[(r"/", IndexHandler)])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()