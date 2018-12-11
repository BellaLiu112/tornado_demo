import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.gen
import tornado.web
import tornado.queues
from tornado.ioloop import IOLoop
from tornado.queues import Queue
import time
import threading

def current_time_mills():
    return int(round(time.time() * 1000))

request_users = {}
class User(object) :
    def __init__(self):
       self.last_visit_time = 0
       self.req_num = 0

process_queue = Queue(maxsize=5000)
con = threading.Condition()

class RequestProcessThread(threading.Thread):
    def run(self):
        con.acquire()

async def handle_request(req_handler):
    remote_ip = req_handler.request.remote_ip
    message = "Hello, world {}".format(remote_ip);
    if req_handler.active():
      req_handler.write(message)
    req_handler.finish()

class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    #@tornado.gen.coroutine
    def get(self):
        user = request_users[self.request.remote_ip]
        if user == None:
            user = User()
            request_users[self.request.remote_ip] = user
        diff = current_time_mills() - user.last_visit_time
        if (diff < 1000) :
            if (user.req_num > 10):
                self.write("Visit too frequently")
                self.finish()
                return
            else:
                user.req_num = user.req_num + 1
        else:
            user.last_visit_time = current_time_mills()
            user.req_num = 1

        if process_queue.full():
            self.write("server overflow")
            self.finish()
            return

        process_queue.put_nowait(self)

    def post(self):
        self.write("Hello, world")

def clean_timeout_users():
    current_time = current_time_mills()
    for key in request_users:
        if current_time - request_users[key].last_visit_time > 10 * 60 * 1000:
            del request_users[key]

    IOLoop.add_timeout(time.time() + 1 * 60 * 1000, clean_timeout_users)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    IOLoop.add_timeout(time.time() + 1 * 60 * 1000, clean_timeout_users)
    IOLoop.current().start()
