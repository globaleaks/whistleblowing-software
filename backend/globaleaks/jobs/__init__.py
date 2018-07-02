from globaleaks.jobs import anomalies, \
                            daily, \
                            delivery, \
                            exit_nodes_refresh, \
                            notification, \
                            onion_service, \
                            pgp_check, \
                            session_management, \
                            statistics, \
                            update_check, \
                            certificate_check

jobs_list = [
    anomalies.Anomalies,
    daily.Daily,
    delivery.Delivery,
    exit_nodes_refresh.ExitNodesRefresh,
    notification.Notification,
    pgp_check.PGPCheck,
    session_management.SessionManagement,
    statistics.Statistics,
    update_check.UpdateCheck,
    certificate_check.CertificateCheck,
]

services_list = [
    onion_service.OnionService
]
