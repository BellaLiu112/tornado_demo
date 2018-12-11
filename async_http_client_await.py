from tornado import gen
from tornado.ioloop import IOLoop
from tornado.queues import Queue
from tornado.httpclient import  AsyncHTTPClient

q = Queue(maxsize=2)
urls = ["http://www.baidu.com", "http://www.google.com", "http://www.qq.com"]

async def get(url):
    http_client = AsyncHTTPClient()
    try:
        response = await http_client.fetch(url)
    except Exception as e:
        print("Error: %s" % e)
    else:
        print(response.body)

async def f():
    for url in urls:
        IOLoop.current().spawn_callback(get, url)

async def consumer():
    async for item in q:
        try:
            print('Doing work on %s' % item)
            await gen.sleep(0.1)
        finally:
            q.task_done()

async def producer():
    for item in range(20):
        await q.put(item)
        print('Put %s' % item)
        await gen.sleep(0.1)

async def main():
    # Start consumer without waiting (since it never finishes).
    IOLoop.current().spawn_callback(consumer)
    IOLoop.current().spawn_callback(f)
    await producer()     # Wait for producer to put all tasks.
    await q.join()       # Wait for consumer to finish all tasks.
    print('Done')

IOLoop.current().run_sync(main)
IOLoop.current().start()