class FakeLogger(object):

    def __init__(self):

        class Log(object):

            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                pass

            def __exit__(self, *args):
                pass

        self.Log = Log

fake_logger = FakeLogger()
