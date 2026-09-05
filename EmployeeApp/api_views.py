from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from .models import Employee
from .serializers import EmployeeSerializer
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.permissions import AllowAny
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes
)
from .models import AuditLog
from .audit import log_activity
from django.contrib.auth.hashers import make_password, check_password
import csv
from django.http import HttpResponse

# def log_activity(request, action, description, user=None):
    
#     username = user.name if user else "Anonymous"
#     role = user.role if user else "Unknown"

#     ip_address = request.META.get("REMOTE_ADDR")

#     AuditLog.objects.create(
#         user=user,
#         username=username,
#         role=role,
#         action=action,
#         description=description,
#         ip_address=ip_address
#     )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def activity_logs_api(request):

    try:

        # ==================================================
        # CHECK CUSTOM DJANGO SESSION
        # ==================================================

        email = request.session.get("email")

        if not email:
            return Response(
                {
                    "status": False,
                    "message": "Authentication required."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ==================================================
        # GET LOGGED-IN EMPLOYEE
        # ==================================================

        try:

            current_employee = Employee.objects.get(
                email=email,
                isDeleted=False
            )

        except Employee.DoesNotExist:

            return Response(
                {
                    "status": False,
                    "message": "Authenticated employee not found."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ==================================================
        # ROLE-BASED ACCESS
        # ==================================================

        current_role = current_employee.role

        if current_role != "Admin":

            return Response(
                {
                    "status": False,
                    "message": "You do not have permission to view activity logs."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # ==================================================
        # GET ACTIVITY LOGS
        # ==================================================

        logs = AuditLog.objects.all().order_by("-timestamp")

        # ==================================================
        # SEARCH
        # ==================================================

        search = request.GET.get(
            "search",
            ""
        ).strip()

        if search:

            logs = logs.filter(
                Q(username__icontains=search) |
                Q(role__icontains=search) |
                Q(action__icontains=search) |
                Q(description__icontains=search) |
                Q(ip_address__icontains=search) 
            )

        # ==================================================
        # ACTION FILTER
        # ==================================================

        action = request.GET.get(
            "action",
            ""
        ).strip()

        if action:

            valid_actions = [
                "LOGIN",
                "LOGOUT",
                "REGISTRATION",
                "CREATE",
                "UPDATE",
                "DELETE",
                "PASSWORD_CHANGE",
            ]

            action = action.upper()

            if action not in valid_actions:

                return Response(
                    {
                        "status": False,
                        "message": "Invalid action filter."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            logs = logs.filter(
                action=action
            )

        # ==================================================
        # ROLE FILTER
        # ==================================================

        role = request.GET.get(
            "role",
            ""
        ).strip()

        if role:

            valid_roles = [
                "Admin",
                "User"
            ]

            if role not in valid_roles:

                return Response(
                    {
                        "status": False,
                        "message": "Invalid role filter."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            logs = logs.filter(
                role=role
            )

        # ==================================================
        # PAGINATION VALIDATION
        # ==================================================

        page_number = request.GET.get(
            "page",
            "1"
        )

        page_size = request.GET.get(
            "page_size",
            "10"
        )

        try:

            page_number = int(page_number)

            page_size = int(page_size)

        except (ValueError, TypeError):

            return Response(
                {
                    "status": False,
                    "message": "Page and page_size must be numbers."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if page_number < 1:

            return Response(
                {
                    "status": False,
                    "message": "Page must be greater than 0."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if page_size < 1 or page_size > 100:

            return Response(
                {
                    "status": False,
                    "message": "Page size must be between 1 and 100."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ==================================================
        # PAGINATION
        # ==================================================

        paginator = Paginator(
            logs,
            page_size
        )

        if (
            paginator.num_pages > 0
            and page_number > paginator.num_pages
        ):

            return Response(
                {
                    "status": False,
                    "message": "Page number exceeds available pages."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        page_obj = paginator.get_page(
            page_number
        )

        # ==================================================
        # RESPONSE DATA
        # ==================================================

        log_data = []

        for log in page_obj:

            log_data.append(
                {
                    "id": log.id,
                    "username": log.username,
                    "role": log.role,
                    "action": log.action,
                    "description": log.description,
                    "ip_address": log.ip_address,
                    "timestamp": log.timestamp,
                }
            )

        # ==================================================
        # FINAL RESPONSE
        # ==================================================

        return Response(
            {
                "status": True,
                "message": "Activity logs fetched successfully.",
                "data": log_data,
                "pagination": {
                    "current_page": page_obj.number,
                    "page_size": page_size,
                    "total_records": paginator.count,
                    "total_pages": paginator.num_pages,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous(),
                }
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:

        print(
            f"Activity Log API Error: {str(e)}"
        )

        return Response(
            {
                "status": False,
                "message": "An error occurred while fetching activity logs.",
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def activity_logs_export_csv(request):

    try:
        # ==========================================
        # SESSION AUTHENTICATION
        # ==========================================

        if "email" not in request.session:
            return Response(
                {
                    "status": False,
                    "message": "Authentication required."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ==========================================
        # ROLE CHECK
        # ==========================================

        current_role = request.session.get("role")

        if current_role != "Admin":
            return Response(
                {
                    "status": False,
                    "message": "You do not have permission to export activity logs."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # ==========================================
        # GET LOGS
        # ==========================================

        logs = AuditLog.objects.all().order_by("-timestamp")

        # ==========================================
        # SEARCH FILTER
        # ==========================================

        search = request.GET.get("search", "").strip()

        if search:
            logs = logs.filter(
                Q(username__icontains=search) |
                Q(role__icontains=search) |
                Q(action__icontains=search) |
                Q(description__icontains=search) |
                Q(ip_address__icontains=search)
            )

        # ==========================================
        # ACTION FILTER
        # ==========================================

        action = request.GET.get("action", "").strip()

        if action:

            valid_actions = [
                "LOGIN",
                "LOGOUT",
                "REGISTRATION",
                "CREATE",
                "UPDATE",
                "DELETE",
                "PASSWORD_CHANGE",
            ]

            action = action.upper()

            if action not in valid_actions:
                return Response(
                    {
                        "status": False,
                        "message": "Invalid action filter."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            logs = logs.filter(action=action)

        # ==========================================
        # ROLE FILTER
        # ==========================================

        role = request.GET.get("role", "").strip()

        if role:

            valid_roles = [
                "Admin",
                "User"
            ]

            if role not in valid_roles:
                return Response(
                    {
                        "status": False,
                        "message": "Invalid role filter."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            logs = logs.filter(role=role)

        # ==========================================
        # CREATE CSV RESPONSE
        # ==========================================

        response = HttpResponse(
            content_type="text/csv"
        )

        response["Content-Disposition"] = (
            'attachment; filename="activity_logs.csv"'
        )

        writer = csv.writer(response)

        # ==========================================
        # CSV HEADER
        # ==========================================

        writer.writerow([
            "ID",
            "User",
            "Role",
            "Action",
            "Description",
            "IP Address",
            "Timestamp"
        ])

        # ==========================================
        # CSV DATA
        # ==========================================

        for log in logs:

            writer.writerow([
                log.id,
                log.username,
                log.role,
                log.action,
                log.description,
                log.ip_address,
                log.timestamp
            ])

        return response

    except Exception as e:

        print(
            f"Activity Log CSV Export Error: {str(e)}"
        )

        return Response(
            {
                "status": False,
                "message": "Unable to export activity logs.",
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def signin_api(request):
    print("REQUEST DATA =", request.data)
    
    email = request.data.get("email")
    password = request.data.get("password")

    # ==============================
    # VALIDATION
    # ==============================

    if not email or not password:
        return Response(
            {
                "status": False,
                "message": "Email and Password are required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ==============================
    # FIND EMPLOYEE
    # ==============================

    try:
        employee = Employee.objects.get(
            email=email,
            isDeleted=False
        )

    except Employee.DoesNotExist:
        return Response(
            {
                "status": False,
                "message": "Invalid Email or Password."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # ==============================
    # CHECK PASSWORD
    # ==============================

    if not check_password(password, employee.password):
        return Response(
            {
                "status": False,
                "message": "Invalid Email or Password."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # ==============================
    # CREATE JWT TOKEN
    # ==============================

    refresh = RefreshToken.for_user(employee)

    refresh["email"] = employee.email
    refresh["name"] = employee.name
    refresh["role"] = employee.role

    access_token = refresh.access_token

    # ==============================
    # CREATE LOGIN ACTIVITY LOG
    # ==============================

    log_activity(
        request=request,
        action="LOGIN",
        description=f"{employee.name} logged in successfully",
        user=employee
    )

    # ==============================
    # RESPONSE
    # ==============================

    return Response(
        {
            "status": True,
            "message": "Login Successful",

            "tokens": {
                "refresh": str(refresh),
                "access": str(access_token)
            },

            "data": {
                "id": employee.id,
                "name": employee.name,
                "email": employee.email,
                "role": employee.role
            }
        },
        status=status.HTTP_200_OK
    )
#========================================================================================


@api_view(["POST"])
def signup_api(request):

    print(request.data)  

    data = request.data.copy()

    password = data.get("password")

    if not password:
        return Response(
            {
                "status": False,
                "message": "Password is required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    data["password"] = make_password(password)

    serializer = EmployeeSerializer(data=data)

    if serializer.is_valid():
            
            employee = serializer.save()

            log_activity(
                request=request,
                action="REGISTRATION",
                description=f"Employee {employee.name} registered successfully",
                user=employee
            )

            return Response(
                {
                    "status": True,
                    "message": "Employee Registered Successfully",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#========================================================================================

@api_view(["POST"])
def signout_api(request):
    email = request.data.get("email")
    password = request.data.get("password")
    
    if not email or not password:
        return Response(
            {
                "status": False,
                "message": "Email and Password are required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        employee = Employee.objects.get(email=email)
    except Employee.DoesNotExist:
        return Response(
            {
                "status": False,
                "message": "Invalid Email or Password."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    if not check_password(password, employee.password):
        return Response(
            {
                "status": False,
                "message": "Invalid Email or Password."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    log_activity(
        request=request,
        action="LOGOUT",
        description=f"{employee.name} logged out successfully",
        user=employee
    )

    return Response(
        {
            "status": True,
            "message": "Sign-out successful."
        },
        status=status.HTTP_200_OK
    )
#========================================================================================



@api_view(["POST"])
def add_employee_api(request):

    serializer = EmployeeSerializer(data=request.data)

    if serializer.is_valid():

        employee = serializer.save()

        log_activity(
            request=request,
            action="CREATE",
            description=f"Employee {employee.name} was created",
            user=employee
        )

        return Response(
            {
                "status": True,
                "message": "Employee Added Successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    return Response(
        {
            "status": False,
            "message": "Employee creation failed.",
            "errors": serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


#========================================================================================

@api_view(["GET"])
def get_all_employee_api(request):

    employees = Employee.objects.filter(isDeleted=False)

    serializer = EmployeeSerializer(employees,many=True)

    return Response(
        {
            "status":True,
            "count":employees.count(),
            "data":serializer.data
        },
        status=status.HTTP_200_OK
    )
    
#========================================================================================

@api_view(["GET"])
def get_employee_api(request, email):

    try:
        employee = Employee.objects.get(email=email)

    except Employee.DoesNotExist:

        return Response(
            {
                "status": False,
                "message": "Employee Not Found"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = EmployeeSerializer(employee)

    return Response(
        {
            "status": True,
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )

#========================================================================================

@api_view(["DELETE"])
def delete_employee_api(request, email):
    try:
        employee = Employee.objects.get(email=email)
    except Employee.DoesNotExist:
        return Response(
            {"message": "Employee Not Found"},
            status=status.HTTP_404_NOT_FOUND
        )

    employee.isDeleted = True
    employee.status = "Inactive"
    employee.save()

    log_activity(
        request=request,
        action="DELETE",
        description=f"Employee {employee.name} was deleted",
        user=employee
    )

    return Response(
        {
            "status": True,
            "message": "Employee Deleted Successfully"
        },
        status=status.HTTP_200_OK
    )
#========================================================================================

@api_view(["PUT"])
def update_user(request, email):
    try:
        employee = Employee.objects.get(email=email)
    except Employee.DoesNotExist:
        return Response(
            {"message": "Employee Not Found"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = EmployeeSerializer(
        employee,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
    
        employee = serializer.save()

        log_activity(
            request=request,
            action="UPDATE",
            description=f"Employee {employee.name} was updated",
            user=employee
        )

        return Response(
            {
                "message": "Employee Updated Successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete_user(request, email):
    try:
        employee = Employee.objects.get(email=email)
    except Employee.DoesNotExist:
        return Response(
            {"message": "Employee Not Found"},
            status=status.HTTP_404_NOT_FOUND
        )

    employee.isDeleted = True
    employee.status = "Inactive"
    employee.save()

    log_activity(
        request=request,
        action="DELETE",
        description=f"Employee {employee.name} was deleted",
        user=employee
    )

    return Response(
        {
            "status": True,
            "message": "Deleted Successfully"
        },
        status=status.HTTP_200_OK
    )
        


@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def dashboard_api(request):

    # ==========================================
    # GET JWT TOKEN
    # ==========================================

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return Response(
            {
                "status": False,
                "message": "Authorization token is required."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not auth_header.startswith("Bearer "):
        return Response(
            {
                "status": False,
                "message": "Invalid authorization header."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # ==========================================
    # VALIDATE JWT
    # ==========================================

    try:

        token = auth_header.split(" ")[1]

        jwt_auth = JWTAuthentication()

        validated_token = jwt_auth.get_validated_token(token)

        # Get custom email claim from JWT
        email = validated_token.get("email")

        if not email:
            return Response(
                {
                    "status": False,
                    "message": "Email not found in token."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ==========================================
        # FIND EMPLOYEE
        # ==========================================

        employee = Employee.objects.get(
            email=email,
            isDeleted=False
        )

    except Employee.DoesNotExist:

        return Response(
            {
                "status": False,
                "message": "Employee not found."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    except Exception as e:

        return Response(
            {
                "status": False,
                "message": "Invalid or expired token.",
                "error": str(e)
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # ==========================================
    # DASHBOARD DATA
    # ==========================================

    total = Employee.objects.filter(
        isDeleted=False
    ).count()

    active = Employee.objects.filter(
        isDeleted=False,
        status="Active"
    ).count()

    recent = Employee.objects.filter(
        isDeleted=False,
        created_date__date=timezone.now().date()
    ).count()

    department = Employee.objects.filter(
        isDeleted=False
    ).values(
        "department"
    ).annotate(
        total=Count("department")
    )

    gender = Employee.objects.filter(
        isDeleted=False
    ).values(
        "gender"
    ).annotate(
        total=Count("gender")
    )

    # ==========================================
    # RESPONSE
    # ==========================================

    return Response(
        {
            "status": True,
            "message": "Welcome to Dashboard",

            "user": {
                "id": employee.id,
                "name": employee.name,
                "email": employee.email,
                "role": employee.role
            },

            "total_employees": total,

            "active_employees": active,

            "recent_employees": recent,

            "department": list(department),

            "gender": list(gender)
        },
        status=status.HTTP_200_OK
    )