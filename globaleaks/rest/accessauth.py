import datetime

# TODO: Log system
# TODO: the DBIO.resume is wrong, acctually. The goal:
#       DO NOT IMPORT SQLALCHEMY HERE
#       DO NOT IMPORT SQLALCHEMY HERE

def verify_whistleblower(receipt):
    """
    return the WhistleblowerTip instance, and perform the right authentication
    method of the receipt
    """
    # complex salt+hashing mechanism can be implemented here
    resuming_secret = receipt

    WTip = DBIO.resume('WhistleblowerTip', secret_id, resuming_secret)
    NodeO = DBIO.resume('Node', None, None)

    if not WTip:
        NodeO.wrong_wb_auth = (1 + NodO.wrong_wb_auth)
        return None

    # Field update 
    NodO.wb_access_count = (1 + NodO.wb_access_count)
    WTip.last_access = datetime.datetime.now()
    WTip.access_count = (1 + WTip.access_count)

    return WTip

def verify_receiver(t_secret):
    """
    Verification of the secret possessed by the receiver, and return ReceiverTip
    """
    ReTip = DBIO.resume('ReceiverTip', secret_id, t_secret)
    NodeO = DBIO.resume('Node', None, None)

    if not ReTip:
        NodeO.wrong_rcvr_auth = ( 1 + Node0.wrong_rcvr_auth)
        return None

    ReTip.access_count = (1 + ReTip.access_count)
    ReTip.last_access = datetime.datetime.now()

    return ReTip
