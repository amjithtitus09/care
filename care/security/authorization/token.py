from care.security.authorization import AuthorizationController
from care.security.authorization.base import AuthorizationHandler
from care.security.permissions.token import TokenPermissions


class TokenCategoryAccess(AuthorizationHandler):
    def can_list_facility_token_category(self, user, facility):
        """
        Check if the user has permission to view token category in the facility
        """
        return self.check_permission_in_facility_organization(
            [TokenPermissions.can_list_token_category.name],
            user,
            facility=facility,
        )

    def can_write_facility_token_category(self, user, facility):
        """
        Check if the user has permission to view token category in the facility
        """
        return self.check_permission_in_facility_organization(
            [TokenPermissions.can_write_token_category.name],
            user,
            facility=facility,
            root=True,
        )


AuthorizationController.register_internal_controller(TokenCategoryAccess)
