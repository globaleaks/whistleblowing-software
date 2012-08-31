class SubmissionValidator(object):
    @classmethod
    def validate(*args, **kw):
        print args
        print kw
        return True

    @classmethod
    def files(*args, **kw):
        return True

class TipValidator(object):
    @classmethod
    def validate(*args, **kw):
        return True

class ReceiverValidator(object):
    @classmethod
    def validate(*args, **kw):
        return True

class AdminValidator(object):
    @classmethod
    def validate(*args, **kw):
        return True

