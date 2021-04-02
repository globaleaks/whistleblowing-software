# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

import warnings


class FSM(object):
    """
    Pass callables for matcher and handler to add_handler to create
    transitions between states. A "matcher" is a predicate, and if a
    transition handles something, it returns the next state.

    If you want something to track global state, put it in your data
    instance passed to process so that transitions and states can
    access it.

    Example:
    idle = State("IDLE")
    stuff = State("STUFF")

    def is_capital(letter):
        return letter in string.uppercase

    def is_small(letter):
        return letter in string.lowercase

    def do_something_with_capitals(letter):
        print("Got capital:", letter)
        return stuff

    idle.add_transition(
        Transition(stuff, is_capital, self.do_something_with_capitals)
    )
    stuff.add_transition(
        Transition(idle, is_lower, None)
    )
    """

    states = []
    state = None

    def __init__(self, states):
        """first state is the initial state"""
        if len(states) > 0:
            self.state = states[0]
        self.states = states

    def process(self, data):
        if self.state is None:
            raise RuntimeError("There is no initial state.")
        next_state = self.state.process(data)
        if next_state:
            self.state = next_state
        else:
            warnings.warn("No next state", RuntimeWarning)

    def add_state(self, state):
        # first added state is initial state
        if len(self.states) == 0:
            self.state = state
        self.states.append(state)

    def dotty(self):
        r = 'digraph fsm {\n\n'
        for s in self.states:
            r = r + s.dotty()
        r = r + '\n}\n'
        return r


class State(object):
    def __init__(self, name):
        self.name = name
        self.transitions = []

    def process(self, data):
        for t in self.transitions:
            r = t.process(data)
            if r is not None:
                return r
        return None

    def add_transition(self, t):
        self.transitions.append(t)
        t.start_state = self

    def add_transitions(self, transitions):
        for t in transitions:
            self.add_transition(t)

    def __str__(self):
        r = '<State %s [' % self.name
        for t in self.transitions:
            r = r + (' ->%s ' % t.next_state.name)
        r = r + ']>'
        return r

    def dotty(self):
        r = '%s;\n' % self.name
        r = r + 'edge [fontsize=8]\n'
        r = r + 'rankdir=TB;\nnodesep=2;\n'
        for t in self.transitions:
            r = r + '%s -> %s [label="%s\\n%s"]\n' % (self.name,
                                                      t.next_state.name,
                                                      t.matcher.__name__,
                                                      t.handler.__name__)
        return r


class Transition(object):
    def __init__(self, next_state, matcher, handler):
        self.matcher = matcher
        self.handler = handler
        self.start_state = None
        self.next_state = next_state
        if self.next_state is None:
            raise RuntimeError("next_state must be valid")

    def match(self, data):
        """
        used by process; calls handler if matcher returns true for
        data by default. may override instead of providing a matcher
        methdo to ctor.
        """
        if self.matcher is not None:
            return self.matcher(data)
        return True

    def handle(self, data):
        """
        return next state. May override in a subclass to change
        behavior or pass a handler method to ctor
        """
        if self.handler:
            state = self.handler(data)
            if state is None:
                return self.next_state
            return state
        return self.next_state

    def process(self, data):
        """return next state, or None if not handled."""
        if self.match(data):
            return self.handle(data)
        return None

    def __str__(self):
        if self.start_state:
            return "<Transition %s->%s>" % (self.start_state.name,
                                            self.next_state.name)
        return "<Transition ->%s>" % (self.next_state.name,)
