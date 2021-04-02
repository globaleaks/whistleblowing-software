from __future__ import print_function

import txtorcon.spaghetti
from txtorcon.spaghetti import State
from txtorcon.spaghetti import Transition
from txtorcon.spaghetti import FSM
from twisted.trial import unittest

import os
import subprocess
import tempfile


class FsmTests(unittest.TestCase):

    def match(self, data):
        if data.split()[0] == '250':
            return True
        return False

    def test_reprs(self):
        """
        not really 'testing' here, going for code-coverage to simply
        call the __str__ methods to ensure they don't explode
        """

        a = State("A")
        b = State("B")
        tran = Transition(b, lambda x: None, lambda x: None)
        a.add_transition(tran)
        fsm = FSM([a, b])
        str(fsm)
        str(a)
        str(tran)
        tran.start_state = None
        str(tran)
        fsm.dotty()

    def test_no_init(self):
        fsm = FSM([])
        self.assertRaises(Exception, fsm.process, "")

    def test_no_init_ctor(self):
        fsm = FSM([])
        idle = State("I")
        str(idle)
        fsm.add_state(idle)
        self.assertWarns(RuntimeWarning, "No next state",
                         txtorcon.spaghetti.__file__, fsm.process, "")

    def test_two_states(self):
        fsm = FSM([])
        idle = State("I")
        notidle = State("N")
        fsm.add_state(idle)
        fsm.add_state(notidle)

    def test_no_matcher(self):
        idle = State("I")
        other = State("O")
        fsm = FSM([idle, other])

        idle.add_transition(Transition(other, None, None))
        fsm.process("")

    def test_bad_transition(self):
        self.assertRaises(Exception, Transition, None, self.match, None)

    def test_dotty(self):
        idle = State("I")
        fsm = FSM([idle])
        self.assertTrue(idle.dotty() in fsm.dotty())
        self.assertTrue("digraph" in fsm.dotty())
        fname = tempfile.mktemp() + '.dot'
        try:
            f = open(fname, 'w')
            f.write(fsm.dotty())
            f.close()
            try:
                proc = subprocess.Popen(('dot', fname),
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            except OSError:
                # Graphviz probably not available; skip
                return
            else:
                _, stderr = proc.communicate()
                retcode = proc.poll()
                if retcode:
                    self.fail('Calling dot returned %i (%s)' % (retcode,
                                                                stderr))
        finally:
            os.unlink(fname)

    def test_handler_state(self):
        idle = State("I")
        cmd = State("C")

        idle.add_transitions([Transition(cmd,
                                         self.match,
                                         lambda x: idle)])

        fsm = FSM([idle, cmd])
        self.commands = []
        self.assertEqual(fsm.state, idle)
        fsm.process("250 OK\n")
        self.assertEqual(fsm.state, idle)

    def test_simple_machine(self):
        idle = State("I")
        cmd = State("C")

        idle.add_transitions([Transition(cmd,
                                         self.match,
                                         None)])

        fsm = FSM([idle, cmd])
        self.commands = []
        self.assertEqual(fsm.state, idle)
        fsm.process("250 OK\n")
        self.assertEqual(fsm.state, cmd)

    def doCommand(self, data):
        print("transition:", data)
