import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.gen
import tornado.web
import tornado.queues
from tornado.ioloop import IOLoop
from tornado.queues import Queue
import time


def current_time_mills():
    return int(round(time.time() * 1000))


request_users = {}


class User(object) :
    def __init__(self):
       self.last_visit_time = 0
       self.req_num = 0

index = 0
pending_queue = Queue(maxsize=20)
request_queue = Queue(maxsize=5000)


async def process_pending():
    while True:
        req_handler = await pending_queue.get()
        print("get request from pending queue")
        try:
           global index
           remote_ip = req_handler.request.remote_ip
           message = "Hello, world {} {}".format(remote_ip, index)
           index = index + 1
           #process grpc here
           req_handler.write(message)
           req_handler.finish()
        except Exception as e:
            print('Exception: %s' % e)
        finally:
            pending_queue.task_done()


async def process_request():
    while True:
        req_handler = await request_queue.get()
        print("get request from request queue")
        try:
           print("put request into pending queue")
           await pending_queue.put(req_handler)
        except Exception as e:
            print('Exception: %s' % e)
        finally:
            request_queue.task_done()


class MainHandler(tornado.web.RequestHandler):
    async def get(self):
        user = request_users.get(self.request.remote_ip)
        if user == None:
            user = User()
            request_users.setdefault(self.request.remote_ip, user)
        diff = current_time_mills() - user.last_visit_time
        if diff < 1000:
            if user.req_num > 10:
                self.write("Visit too frequently")
                self.finish()
                return
            else:
                user.req_num = user.req_num + 1
        else:
            user.last_visit_time = current_time_mills()
            user.req_num = 1

        if request_queue.full():
            self.write("server overflow")
            self.finish()
            return

        await request_queue.put(self)

    async def post(self):
        self.write("Hello, world")

def clean_timeout_users():
    print("clean timeout users")
    current_time = current_time_mills()
    for key in request_users:
        if current_time - request_users[key].last_visit_time > 10 * 60 * 1000:
            print("del %s", key)
            del request_users[key]

    IOLoop.add_timeout(IOLoop.current(), deadline=time.time() + 1 * 60 * 1000, callback=clean_timeout_users)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8889)
    IOLoop.add_timeout(IOLoop.current(),deadline=time.time() + 1 * 60 * 1000, callback=clean_timeout_users)
    IOLoop.current().spawn_callback(process_request)
    IOLoop.current().spawn_callback(process_pending)
    IOLoop.current().start()
