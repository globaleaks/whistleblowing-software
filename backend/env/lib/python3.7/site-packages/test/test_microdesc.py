
from twisted.trial import unittest

from txtorcon._microdesc_parser import MicrodescriptorParser


class ParserTests(unittest.TestCase):

    def test_two_no_w(self):
        relays = []

        def create_relay(**kw):
            relays.append(kw)
        m = MicrodescriptorParser(create_relay)

        for line in [
                'r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 11.11.11.11 443 80',
                's Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof',
                'r ekaf foooooooooooooooooooooooooo barbarbarbarbarbarbarbarbar 2011-11-11 16:30:00 22.22.22.22 443 80',
                's Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof',
        ]:
            m.feed_line(line)
        m.done()

        self.assertEqual(2, len(relays))
        self.assertEqual('fake', relays[0]['nickname'])
        self.assertEqual('ekaf', relays[1]['nickname'])
        self.assertEqual('11.11.11.11', relays[0]['ip'])
        self.assertEqual('22.22.22.22', relays[1]['ip'])

        self.assertTrue('bandwidth' not in relays[0])
        self.assertTrue('bandwidth' not in relays[1])
        self.assertTrue('flags' in relays[0])
        self.assertTrue('flags' in relays[1])
        self.assertTrue('FutureProof' in relays[1]['flags'])

    def test_two(self):
        relays = []

        def create_relay(**kw):
            relays.append(kw)
        m = MicrodescriptorParser(create_relay)

        for line in [
                'r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 11.11.11.11 443 80',
                's Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof',
                'r ekaf foooooooooooooooooooooooooo barbarbarbarbarbarbarbarbar 2011-11-11 16:30:00 22.22.22.22 443 80',
                's Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof',
                'w Bandwidth=518000',
                'p accept 43,53,79-81',
        ]:
            m.feed_line(line)
        m.done()

        self.assertEqual(2, len(relays))
        self.assertEqual('fake', relays[0]['nickname'])
        self.assertEqual('ekaf', relays[1]['nickname'])
        self.assertEqual('11.11.11.11', relays[0]['ip'])
        self.assertEqual('22.22.22.22', relays[1]['ip'])

        self.assertTrue('bandwidth' not in relays[0])
        self.assertTrue('bandwidth' in relays[1])
        self.assertTrue('flags' in relays[0])
        self.assertTrue('flags' in relays[1])
        self.assertTrue('FutureProof' in relays[1]['flags'])

    # re-enable when we switch back to Automat
    def test_bad_line(self):
        relays = []

        def create_relay(**kw):
            relays.append(kw)
        m = MicrodescriptorParser(create_relay)

        with self.assertRaises(Exception) as ctx:
            m.feed_line('x blam')
        # self.assertTrue('Unknown microdescriptor' in str(ctx.exception))
        self.assertTrue('Expected "r " ' in str(ctx.exception))
        self.assertEqual(0, len(relays))

    def test_single_ipv6(self):
        relays = []

        def create_relay(**kw):
            relays.append(kw)
        m = MicrodescriptorParser(create_relay)

        for line in [
                'r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 11.11.11.11 443 80',
                'a [2001:0:0:0::0]:4321'
        ]:
            m.feed_line(line)
        m.done()

        self.assertEqual(1, len(relays))
        self.assertEqual(['[2001:0:0:0::0]:4321'], list(relays[0]['ip_v6']))
