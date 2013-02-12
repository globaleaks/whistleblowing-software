from globaleaks.transactors.base import MacroOperation

from globaleaks.settings import transact
from globaleaks.models.receiver import Receiver
from globaleaks.models.externaltip import ReceiverTip
from globaleaks.rest.errors import ForbiddenOperation, InvalidInputFormat
from globaleaks import settings

class AuthOperations(MacroOperation):

    @transact
    def authenticate_receiver(self, valid_tip):
        receivertip_iface = ReceiverTip(self.store)

        receivers_map = receivertip_iface.get_receivers_by_tip(valid_tip)
        user = receivers_map['actor']

        self.returnData(user)
        self.returnCode(200)
        return self.prepareRetVals()

