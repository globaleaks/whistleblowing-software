# -*- coding: utf-8 -*-
import enum

class _Enum(enum.Enum):
    @classmethod
    def keys(cls):
        return [e.name for e in cls]


class EnumUserRole(_Enum):
    admin = 0
    receiver = 1
    custodian = 2


class EnumUserState(_Enum):
    disabled = 0
    enabled = 1


class EnumContextStatus(_Enum):
    disabled = 0
    enabled = 1
    hidden = 2


class EnumFieldInstance(_Enum):
    instance = 0
    template = 1
    reference = 2


class EnumFieldAttrType(_Enum):
    int = 0
    bool = 1
    unicode = 2
    localized = 3


class EnumFieldOptionScoreType(_Enum):
    none = 0
    addition = 1
    multiplier = 2


class EnumMessageType(_Enum):
    whistleblower = 0
    receiver = 1


class EnumFileStatus(_Enum):
    processing = 0
    reference = 1
    encrypted = 2
    unavailable = 3
