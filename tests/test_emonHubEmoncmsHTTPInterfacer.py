import mock
import time
import unittest

import interfacers.EmonHubEmoncmsHTTPInterfacer
import interfacers.Cargo


class OkResponse:
    def read(self):
        return TestEmonHubEmoncmsHTTPInterfacer.ok


class PauseOkResponse:
    def read(self):
        time.sleep(TestEmonHubEmoncmsHTTPInterfacer.sendinterval - 2)
        return TestEmonHubEmoncmsHTTPInterfacer.ok


class NotOkResponse:
    def read(self):
        return TestEmonHubEmoncmsHTTPInterfacer.not_ok


class TestEmonHubEmoncmsHTTPInterfacer(unittest.TestCase):

    sendinterval = 7
    ok = 'ok'
    not_ok = 'not ok'

    def init(self):
        interfacer = interfacers.EmonHubEmoncmsHTTPInterfacer.EmonHubEmoncmsHTTPInterfacer('test')

        interfacer._settings['apikey'] = '01234567890123456789012345678901'

        interfacer._settings['sendinterval'] = TestEmonHubEmoncmsHTTPInterfacer.sendinterval

        interfacer.queue.clear()

        return interfacer

    def sleep(self, increment):
        time.sleep(TestEmonHubEmoncmsHTTPInterfacer.sendinterval + increment)

    def send(self, interfacer):
        cargo = interfacers.Cargo.new_cargo()
        interfacer.receiver(cargo)

    @mock.patch("interfacers.EmonHubEmoncmsHTTPInterfacer.urllib2.urlopen")
    def test_send_success(self, urlopen_mock):
        interfacer = self.init()

        urlopen_mock.return_value = OkResponse()

        self.send(interfacer)

        self.sleep(TestEmonHubEmoncmsHTTPInterfacer.sendinterval)

        interfacer.action()

        self.assertIs(interfacer.queue.count(), 0)
        self.assertIs(interfacer.buffer.__len__(), 0)

    @mock.patch("interfacers.EmonHubEmoncmsHTTPInterfacer.urllib2.urlopen")
    def test_send_fail(self, urlopen_mock):
        interfacer = self.init()

        urlopen_mock.return_value = NotOkResponse()

        self.send(interfacer)

        self.assertIs(interfacer.buffer.__len__(), 1)

        self.sleep(TestEmonHubEmoncmsHTTPInterfacer.sendinterval)

        interfacer.action()

        self.assertIs(interfacer.queue.count(), 1)
        self.assertIs(interfacer.buffer.__len__(), 0)

    @mock.patch("interfacers.EmonHubEmoncmsHTTPInterfacer.urllib2.urlopen")
    def test_send_recover(self, urlopen_mock):
        interfacer = self.init()

        self.send(interfacer)
        self.send(interfacer)
        self.send(interfacer)

        self.assertIs(interfacer.buffer.__len__(), 3)

        self.sleep(TestEmonHubEmoncmsHTTPInterfacer.sendinterval)

        urlopen_mock.return_value = NotOkResponse()
        interfacer.action()

        self.assertIs(interfacer.queue.count(), 1)
        self.assertIs(interfacer.buffer.__len__(), 0)

        self.send(interfacer)
        self.send(interfacer)
        self.send(interfacer)
        self.send(interfacer)

        self.assertIs(interfacer.queue.count(), 1)
        self.assertIs(interfacer.buffer.__len__(), 4)

        self.sleep(TestEmonHubEmoncmsHTTPInterfacer.sendinterval)

        urlopen_mock.return_value = OkResponse()
        interfacer.action()

        self.assertIs(interfacer.queue.count(), 0)
        self.assertIs(interfacer.buffer.__len__(), 0)

    @mock.patch("interfacers.EmonHubEmoncmsHTTPInterfacer.urllib2.urlopen")
    def test_send_queue_timeout(self, urlopen_mock):
        interfacer = self.init()

        self.send(interfacer)
        self.send(interfacer)
        self.send(interfacer)

        self.assertIs(interfacer.buffer.__len__(), 3)

        time.sleep(TestEmonHubEmoncmsHTTPInterfacer.sendinterval)

        print('add one to queue')
        urlopen_mock.return_value = NotOkResponse()
        interfacer.action()

        self.assertIs(interfacer.queue.count(), 1)
        self.assertIs(interfacer.buffer.__len__(), 0)

        self.send(interfacer)
        self.send(interfacer)
        self.send(interfacer)
        self.send(interfacer)

        self.assertIs(interfacer.queue.count(), 1)
        self.assertIs(interfacer.buffer.__len__(), 4)

        time.sleep(TestEmonHubEmoncmsHTTPInterfacer.sendinterval)

        print('add one more queue')
        interfacer.action()

        self.assertIs(interfacer.queue.count(), 2)
        self.assertIs(interfacer.buffer.__len__(), 0)

        time.sleep(TestEmonHubEmoncmsHTTPInterfacer.sendinterval)

        print('dequeue one due to timeout')
        # the pause will cause the queue polling loop end
        urlopen_mock.return_value = PauseOkResponse()
        interfacer.action()

        self.assertIs(interfacer.queue.count(), 1)
        self.assertIs(interfacer.buffer.__len__(), 0)

        time.sleep(TestEmonHubEmoncmsHTTPInterfacer.sendinterval)

        print('dequeue remaining')
        urlopen_mock.return_value = OkResponse()
        interfacer.action()

        self.assertIs(interfacer.queue.count(), 0)
        self.assertIs(interfacer.buffer.__len__(), 0)
