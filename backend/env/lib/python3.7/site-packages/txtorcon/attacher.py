import itertools
import heapq

from zope.interface import implementer

from .interface import IStreamAttacher


# note to self: might be better to make this Way Simpler and just say
# "order matters", *or* do a simple sort -- so that we can actually
# remove things.


@implementer(IStreamAttacher)
class PriorityAttacher(object):
    """
    This can fill the role of an IStreamAttacher to which you can add
    and remove "sub" attachers. These are consulted in order and the
    first one to return something besides None wins. We use a "heapq"
    priority queue, with 0 being the "most important" and higher
    numbers indicating less important.

    For example::

        tor = yield txtorcon.connect(..)
        attachers = txtorcon.attacher.PriorityAttacher()

        @implementer(IStreamAttacher)
        class MyAttacher(object):
            def __init__(self, interesting_host, circuit):
                self._host = interesting_host
                self._circuit = circuit

            def attach_stream(self, stream, circuits):
                if stream.target_host == self._host:
                    return self._circuit
                return None

        attachers.add_attacher(MyAttacher('torproject.org', circ1))
        attachers.add_attacher(MyAttacher('meejah.ca', circ2))
    """

    def __init__(self):
        # use only heapq.* to modify this; 0th item is "smallest"
        # item. contains 3-tuples of (priority, number, attacher)
        self._attacher_heap = []
        # need to keep a map so we can delete from the priority-queue :(
        self._attacher_to_entry = dict()
        # need to keep a counter so the sorting has a tie-breaker
        self._counter = itertools.count(0, 1)

    def add_attacher(self, attacher, priority=0):
        """
        Add a new IStreamAttacher at a certain priortiy; lower priority
        values mean more important (that is, 0 is the most important).
        """
        item = [priority, next(self._counter), IStreamAttacher(attacher)]
        self._attacher_to_entry[attacher] = item
        heapq.heappush(self._attacher_heap, item)

    def remove_attacher(self, attacher):
        try:
            item = self._attacher_to_entry.pop(attacher)
        except KeyError:
            raise ValueError(
                "attacher {} not found".format(attacher)
            )
        item[-1] = None  # we can't actually remove it from the heap ...

    def attach_stream_failure(self, stream, fail):
        pass
    # hmm, should we try to remember which attacher answered
    # 'something' for this stream, and then report the failure via
    # it...? or just log all failures here?

    def attach_stream(self, stream, circuits):
        for _, _, attacher in self._attacher_heap:
            if attacher is not None:
                answer = attacher.attach_stream(stream, circuits)
                if answer is not None:
                    return answer
        return None
