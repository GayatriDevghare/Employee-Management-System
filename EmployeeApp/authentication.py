from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings

from .models import Employee


class EmployeeJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):

        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]

            employee = Employee.objects.get(
                id=user_id,
                isDeleted=False
            )

            # Make Employee compatible with DRF IsAuthenticated
            employee.is_authenticated = True
            employee.is_anonymous = False

            return employee

        except Employee.DoesNotExist:
            from rest_framework_simplejwt.exceptions import AuthenticationFailed

            raise AuthenticationFailed(
                "Employee not found",
                code="user_not_found"
            )