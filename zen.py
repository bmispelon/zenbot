from cStringIO import StringIO
from contextlib import closing
import sys

def get_zen():
    capture = StringIO()
    sys.stdout = capture
    sys.modules.pop('this', None)
    import this
    sys.stdout = sys.__stdout__
    with closing(capture):
        return capture.getvalue()

ZEN = get_zen()