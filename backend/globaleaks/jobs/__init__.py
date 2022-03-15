from globaleaks.jobs import anomalies, \
                            certificate_check, \
                            cleaning, \
                            delivery, \
                            notification, \
                            pgp_check, \
                            session_management, \
                            statistics, \
                            update_check

jobs_list = [
    anomalies.Anomalies,
    certificate_check.CertificateCheck,
    cleaning.Cleaning,
    delivery.Delivery,
    notification.Notification,
    pgp_check.PGPCheck,
    session_management.SessionManagement,
    statistics.Statistics,
    update_check.UpdateCheck,
]
