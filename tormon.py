#!/usr/bin/env python

from time import time
import json

import tornado.ioloop
import tornado.web


class Storage(object):

    def get(self, name, begin, end, callback):
        raise NotImplementedError()

    def put(self, name, data, dt, ts, callback):
        raise NotImplementedError()

    def list(self):
        raise NotImplementedError()


class RamStorage(object):

    def __init__(self, length=7*24*60):
        self.storage = {}
        self.length = length

    def get(self, name, count):
        return self.storage[name][-count:]

    def put(self, name, data):
        if name not in self.storage:
            self.storage[name] = [0. for i in range(self.length)]
        data = list(data)
        self.storage[name] = self.storage[name][len(data):] + data

    def list(self):
        return list(self.storage.keys())


class BaseHandler(tornado.web.RequestHandler):
    pass


class MainHandler(BaseHandler):

    def get(self):
        self.render("index.html")


class DataHandler(BaseHandler):

    def get(self):
        name = self.get_argument("name");
        limit = int(self.get_argument("limit", 300))
        self.write(json.dumps(storage.get(name, limit)));

    def post(self):
        for name in self.request.arguments:
            data = list(map(float, self.get_argument(name).split(",")))
            storage.put(name, data)
            events.setdefault(name, []).append((time(), len(data)))
            callbacks = list(pollers.get(name, []))
            for callback in callbacks:
                io_loop.add_callback(callback)


class ListHandler(BaseHandler):

    def get(self):
        self.write(json.dumps(storage.list()))


class PollHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self):
        self.name = self.get_argument('name')
        self.ts = float(self.get_cookie(self.name, time()))
        pollers.setdefault(self.name, []).append(self.callback)

    def callback(self):
        if self.callback not in pollers[self.name]:
            return
        if time() > self.ts + .2:
            limit = sum([count for ts, count in events.get(self.name, [])
                         if ts > self.ts])
            if limit:
                limit = min(300, limit)
                pollers[self.name].remove(self.callback)
                self.set_cookie(self.name, "%f" % time())
                self.write(json.dumps(storage.get(self.name, limit)))
                self.finish()


def check_pollers():
    for name, callbacks in pollers.items():
        for callback in callbacks:
            io_loop.add_callback(callback)


def clear_events():
    global events
    t = time() - 60.
    for key, values in events.items():
        events[key] = [i for i in values if i[0] > t]

storage = RamStorage()
pollers = dict()
events = dict()
io_loop = tornado.ioloop.IOLoop.instance()


application = tornado.web.Application(
    [(r"/", MainHandler),
     (r"/data", DataHandler),
     (r"/list", ListHandler),
     (r"/poll", PollHandler)],
    static_path="static",
    debug=True
)


if __name__ == "__main__":
    application.listen(8888)
    #tornado.ioloop.PeriodicCallback(dump_storage, 10000).start()
    tornado.ioloop.PeriodicCallback(check_pollers, 1000).start()
    tornado.ioloop.PeriodicCallback(clear_events, 10000).start()
    io_loop.start()
