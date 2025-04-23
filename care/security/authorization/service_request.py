from care.security.authorization import AuthorizationController
from care.security.authorization.base import AuthorizationHandler
from care.security.permissions.service_request import ServiceRequestPermissions


class ServiceRequestAccess(AuthorizationHandler):
    def can_list_location_service_request(self, user, location):
        """
        Check if the user has permission to view service requests in the given location
        """

        return self.check_permission_in_facility_organization(
            [ServiceRequestPermissions.can_read_service_request.name],
            user,
            orgs=location.facility_organization_cache,
        )


AuthorizationController.register_internal_controller(ServiceRequestAccess)
