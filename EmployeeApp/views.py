from tracemalloc import start
from urllib import request
import random
import re
from functools import wraps
from django.db.models import Q
from collections import defaultdict

# from datetime import datetime, time
import datetime as dt

from django.core.mail import send_mail
from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import Employee, OTP


from .audit import log_activity






def login_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if "email" not in request.session:
            return redirect("signin")

        return view_func(request, *args, **kwargs)

    return wrapper


def admin_required(view_func):
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if request.session.get("role") != "Admin":
            return redirect("user_dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


def user_required(view_func):
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if request.session.get("role") != "User":
            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper



# Create your views here.
def Home(request):
    return render(request, "home.html")

# =========curd==========

from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import Employee
import datetime
import re

def signup(request):
    print("Method =", request.method)

    if request.method == "POST":
        print("POST Data =", request.POST)

        try:
            # Extract all form data
            role = request.POST.get("role", "User")
            name = request.POST.get("name", "").strip()
            age = request.POST.get("age", "")
            gender = request.POST.get("gender", "Male")
            email = request.POST.get("email", "").strip()
            mobile = request.POST.get("phone", "").strip()
            department = request.POST.get("department", "").strip()
            city = request.POST.get("city", "").strip()
            password = request.POST.get("password", "")
            
            
            # Optional fields
            address_line = request.POST.get("address_line", "").strip()
            department_work = request.POST.get("department_work", "").strip()
            joining_date = request.POST.get("joining_date", "")
            salary = request.POST.get("salary", "")
            
            

            # ===== VALIDATION =====
            
            # 1. Required fields
            required_fields = {
                'role': role,
                'name': name,
                'age': age,
                'gender': gender,
                'email': email,
                'mobile': mobile,
                'password': password,
                'department': department if department else department_work,
                'city': city,
                'joining_date': joining_date,
                'salary': salary,
                'address_line': address_line,
            }
            
            empty_fields = [field for field, value in required_fields.items() if not value]
            if empty_fields:
                error_msg = f"Please fill in: {', '.join(empty_fields)}"
                messages.error(request, error_msg)
                return render(request, "signup.html", {
                    'message': error_msg,
                    'color': '#dc2626'
                })

            # 2. Age validation
            try:
                age = int(age)
                if age < 18 or age > 100:
                    messages.error(request, "Age must be between 18 and 100.")
                    return render(request, "signup.html", {
                        'message': 'Age must be between 18 and 100.',
                        'color': '#dc2626'
                    })
            except ValueError:
                messages.error(request, "Please enter a valid age.")
                return render(request, "signup.html", {
                    'message': 'Please enter a valid age.',
                    'color': '#dc2626'
                })

            # 3. Email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                messages.error(request, "Please enter a valid email address.")
                return render(request, "signup.html", {
                    'message': 'Please enter a valid email address.',
                    'color': '#dc2626'
                })

            # 4. Check existing email
            if Employee.objects.filter(email=email).exists():
                messages.error(request, "An account with this email already exists.")
                return render(request, "signup.html", {
                    'message': 'An account with this email already exists.',
                    'color': '#dc2626'
                })

            # 5. Password validation
            if len(password) < 6:
                messages.error(request, "Password must be at least 6 characters long.")
                return render(request, "signup.html", {
                    'message': 'Password must be at least 6 characters long.',
                    'color': '#dc2626'
                })

            # 6. Mobile validation
            mobile = re.sub(r'\D', '', mobile)  # Remove non-digits
            if len(mobile) < 8 or len(mobile) > 15:
                messages.error(request, "Please enter a valid mobile number (8-15 digits).")
                return render(request, "signup.html", {
                    'message': 'Please enter a valid mobile number (8-15 digits).',
                    'color': '#dc2626'
                })

            # 7. Salary validation (if provided)
            if salary:
                try:
                    salary = float(salary)
                    if salary < 0:
                        messages.error(request, "Salary cannot be negative.")
                        return render(request, "signup.html", {
                            'message': 'Salary cannot be negative.',
                            'color': '#dc2626'
                        })
                except ValueError:
                    messages.error(request, "Please enter a valid salary amount.")
                    return render(request, "signup.html", {
                        'message': 'Please enter a valid salary amount.',
                        'color': '#dc2626'
                    })

            # ===== CREATE EMPLOYEE =====
            
            # Prepare employee data
            employee_data = {
                'role': role,
                'name': name,
                'age': age,
                'gender': gender,
                'email': email,
                'mobile': mobile,
                'city': city,
                'password': make_password(password),
            }

            # Use department from either field
            employee_data['department'] = department if department else department_work

            # Add optional fields if your model supports them
            if address_line:
                employee_data['address'] = address_line
            
            if joining_date:
                try:
                    employee_data['joining_date'] = dt.datetime.strptime(
    joining_date,
    '%Y-%m-%d'
).date()
                except ValueError:
                    pass  # Skip invalid date
            
            if salary:
                employee_data['salary'] = salary

            # Create employee
            employee = Employee.objects.create(**employee_data)

            print(f"✅ Employee Saved: {employee.name} ({employee.email})")

            # Create Registration Activity Log
            log_activity(
                request=request,
                action="REGISTRATION",
                description=f"{employee.name} registered successfully",
                user=employee,
                )
            
            # Success message
            messages.success(request, f"🎉 Account created successfully! Welcome {employee.name}.")
            
            # Redirect to signin
            return redirect("signin")

        except Exception as e:
            print(f"❌ Error creating employee: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, "signup.html", {
                'message': f'Error: {str(e)}',
                'color': '#dc2626'
            })

    # GET request - show signup form
    return render(request, "signup.html")

def signin(request):
    
    if request.method == "POST":

        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        print("================================")
        print("SIGNIN DEBUG")
        print("Email:", email)
        print("Entered Password:", password)

        try:
            employee = Employee.objects.get(
                email=email,
                isDeleted=False
            )

            print("Employee Found:", employee.email)
            print("Database Hash:", employee.password)

            result = check_password(
                password,
                employee.password
            )

            print("check_password result:", result)

            if result:

                print("PASSWORD CORRECT")

                request.session["name"] = employee.name
                request.session["role"] = employee.role
                request.session["email"] = employee.email
                
                log_activity(
                request=request,
                action="LOGIN",
                description=f"{employee.name} logged in successfully",
                user=employee,
                )

                if employee.role == "Admin":
                    return redirect("dashboard")
                else:
                    return redirect("user_dashboard")

            else:

                print("PASSWORD WRONG")

                return render(
                    request,
                    "signin.html",
                    {
                        "message": "Incorrect Password"
                    }
                )

        except Employee.DoesNotExist:

            print("EMAIL NOT FOUND")

            return render(
                request,
                "signin.html",
                {
                    "message": "Email not found"
                }
            )

    return render(request, "signin.html")



def signout(request):
    
    try:
        # Get current logged-in employee before clearing session
        email = request.session.get("email")

        employee = None

        if email:
            try:
                employee = Employee.objects.get(
                    email=email,
                    isDeleted=False
                )
            except Employee.DoesNotExist:
                employee = None

        # Create logout activity log BEFORE flushing session
        log_activity(
            request=request,
            action="LOGOUT",
            description=(
                f"{employee.name} logged out successfully"
                if employee
                else "User logged out successfully"
            ),
            user=employee,
        )

        # Now clear the session
        request.session.flush()

        return redirect("signin")

    except Exception as e:
        print(f"Logout Error: {e}")

        # Even if logging fails, logout should still happen
        request.session.flush()

        return redirect("signin")


@admin_required
@login_required
def dashboard(request):

    if "email" not in request.session:
        return redirect("signin")

    email = request.session.get("email")

    print("Session Email:", email)

    # Fetch logged-in active employee
    employee = Employee.objects.filter(
        email=email,
        isDeleted=False
    ).first()

    if employee is None:
        print("Employee not found for email:", email)

        messages.error(
            request,
            "Employee not found. Please login again."
        )

        request.session.flush()
        return redirect("signin")

    # Total employees
    total = Employee.objects.filter(
        isDeleted=False
    ).count()

    # Active employees
    active_employees = Employee.objects.filter(
        status="Active",
        isDeleted=False
    ).count()

    
    # Employees added today
    today = timezone.localdate()
    
    start = timezone.make_aware(
        dt.datetime.combine(today, dt.time.min)
    )
    
    end = timezone.make_aware(
        dt.datetime.combine(today, dt.time.max)
    )
    
    recent_employees = Employee.objects.filter(
        isDeleted=False,
        created_date__gte=start,
        created_date__lte=end
    ).count()
    
    print("Today:", today)
    print("Start:", start)
    print("End:", end)
    print("Recently Added Count:", recent_employees)


    # Department statistics
    department = Employee.objects.filter(
        isDeleted=False
    ).values(
        "department"
    ).annotate(
        total=Count("department")
    )

    # Gender statistics
    gender = Employee.objects.filter(
        isDeleted=False
    ).values(
        "gender"
    ).annotate(
        total=Count("gender")
    )

    context = {
    "employee": employee,
    "name": employee.name,
    "role": employee.role,
    "total_employees": total,
    "active_employees": active_employees,
    "recent_employees": recent_employees,
    "department": department,
    "gender": gender,
}

    return render(request, "dashboard.html", context)

#=======Total Employees Function========
def total_employees(request):
    
    employees = Employee.objects.filter(isDeleted=False).order_by("-created_date")

    paginator = Paginator(employees, 5)
    page = request.GET.get("page")
    employees = paginator.get_page(page)

    return render(
        request,
        "view_employee.html",
        {
            "employees": employees,
            "title": "Total Employees"
        }
    )

#========Active Employees Function========
# ======== Active Employees Function ========
def active_employees(request):

    employees = Employee.objects.filter(
        isDeleted=False,
        status="Active"
    )

    # Search by name
    search = request.GET.get("search", "").strip()
    if search:
        employees = employees.filter(
            name__icontains=search
        )

    # Status filter
    status = request.GET.get("status", "").strip()
    if status:
        employees = employees.filter(status=status)

    # Role filter
    role = request.GET.get("role", "").strip()
    if role:
        employees = employees.filter(role=role)

    # Sorting
    sort = request.GET.get("sort", "new")

    if sort == "name":
        employees = employees.order_by("name")

    elif sort == "-name":
        employees = employees.order_by("-name")

    elif sort == "new":
        employees = employees.order_by("-created_date")

    elif sort == "old":
        employees = employees.order_by("created_date")

    elif sort == "salary_high":
        employees = employees.order_by("-salary")

    elif sort == "salary_low":
        employees = employees.order_by("salary")

    else:
        employees = employees.order_by("-created_date")

    # Pagination
    paginator = Paginator(employees, 5)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "view_employee.html",
        {
            "employees": page_obj,
            "page_obj": page_obj,
            "title": "Active Employees"
        }
    )


# ======== Recently Added Employees Function ========
def recent_employees(request):

    today = timezone.localdate()

    start = timezone.make_aware(
        dt.datetime.combine(today, dt.time.min)
    )

    end = timezone.make_aware(
        dt.datetime.combine(today, dt.time.max)
    )

    employees = Employee.objects.filter(
        isDeleted=False,
        created_date__gte=start,
        created_date__lte=end
    )

    # Search by name
    search = request.GET.get("search", "").strip()
    if search:
        employees = employees.filter(
            name__icontains=search
        )

    # Status filter
    status = request.GET.get("status", "").strip()
    if status:
        employees = employees.filter(status=status)

    # Role filter
    role = request.GET.get("role", "").strip()
    if role:
        employees = employees.filter(role=role)

    # Sorting
    sort = request.GET.get("sort", "new")

    if sort == "name":
        employees = employees.order_by("name")

    elif sort == "-name":
        employees = employees.order_by("-name")

    elif sort == "new":
        employees = employees.order_by("-created_date")

    elif sort == "old":
        employees = employees.order_by("created_date")

    elif sort == "salary_high":
        employees = employees.order_by("-salary")

    elif sort == "salary_low":
        employees = employees.order_by("salary")

    else:
        employees = employees.order_by("-created_date")

    # Pagination
    paginator = Paginator(employees, 5)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "view_employee.html",
        {
            "employees": page_obj,
            "page_obj": page_obj,
            "title": "Today's Recently Added Employees"
        }
    )




def add_employee(request):
    
    if request.method == "POST":
        print("POST Data =", request.POST)
        
        try:
            # ===== GET ALL FORM DATA =====
            name = request.POST.get("name", "").strip()
            age = request.POST.get("age", "")
            password = request.POST.get("password", "")
            department = request.POST.get("department", "").strip()
            city = request.POST.get("city", "").strip()
            email = request.POST.get("email", "").strip()
            gender = request.POST.get("gender", "Male")
            mobile = request.POST.get("phone", "").strip()
            role = request.POST.get("role", "User")
            
            # New fields from the updated add_employee.html
            address_line = request.POST.get("address_line", "").strip()
            joining_date = request.POST.get("joining_date", "")
            salary = request.POST.get("salary", "")
            
            # ===== VALIDATION =====
            
            # 1. Required fields check
            required_fields = {
                'name': name,
                'age': age,
                'email': email,
                'mobile': mobile,
                'department': department,
                'city': city,
                'password': password,
                'address_line': address_line,
                'joining_date': joining_date,
                'salary': salary
            }
            
            empty_fields = [field for field, value in required_fields.items() if not value]
            if empty_fields:
                error_msg = f"Please fill in all required fields: {', '.join(empty_fields)}"
                return render(request, "add_employee.html", {
                    'error': error_msg,
                    'color': 'red'
                })
            
            # 2. Age validation
            try:
                age = int(age)
                if age < 18 or age > 100:
                    return render(request, "add_employee.html", {
                        'error': 'Age must be between 18 and 100.',
                        'color': 'red'
                    })
            except ValueError:
                return render(request, "add_employee.html", {
                    'error': 'Please enter a valid age.',
                    'color': 'red'
                })
            
            # 3. Email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return render(request, "add_employee.html", {
                    'error': 'Please enter a valid email address.',
                    'color': 'red'
                })
            
            # 4. Check if email already exists
            if Employee.objects.filter(email=email).exists():
                return render(request, "add_employee.html", {
                    'error': 'Employee with this email already exists!',
                    'color': 'red'
                })
            
            # 5. Password validation
            if len(password) < 6:
                return render(request, "add_employee.html", {
                    'error': 'Password must be at least 6 characters long.',
                    'color': 'red'
                })
            
            # 6. Mobile validation
            mobile = re.sub(r'\D', '', mobile)  # Remove non-digits
            if len(mobile) < 8 or len(mobile) > 15:
                return render(request, "add_employee.html", {
                    'error': 'Please enter a valid mobile number (8-15 digits).',
                    'color': 'red'
                })
            
            # 7. Salary validation
            try:
                salary = float(salary)
                if salary < 0:
                    return render(request, "add_employee.html", {
                        'error': 'Salary cannot be negative.',
                        'color': 'red'
                    })
            except ValueError:
                return render(request, "add_employee.html", {
                    'error': 'Please enter a valid salary amount.',
                    'color': 'red'
                })
            
            # 8. Joining date validation
            try:
                if joining_date:
                    joining_date_obj = datetime.datetime.strptime(joining_date, '%Y-%m-%d').date()
                    if joining_date_obj > datetime.date.today():
                        return render(request, "add_employee.html", {
                            'error': 'Joining date cannot be in the future.',
                            'color': 'red'
                        })
            except ValueError:
                return render(request, "add_employee.html", {
                    'error': 'Please enter a valid joining date.',
                    'color': 'red'
                })
            
            # ===== CREATE EMPLOYEE =====
            
            # Hash the password before saving
            hashed_password = make_password(password)
            
            # Create employee with all fields
            employee = Employee.objects.create(
            name=name,
            age=age,
            password=hashed_password,
            department=department,
            city=city,
            email=email,
            gender=gender,
            mobile=mobile,
            role=role,
            address=address_line,
            joining_date=joining_date,
            salary=salary,
            status='Active',
            createdBy=request.session.get('role', 'System'),
            created_date=timezone.now()
)

            print(f"✅ Employee Added: {employee.name} ({employee.email})")

# Create Activity Log
            log_activity(
                request=request,
                action="CREATE",
                description=f"Employee {employee.name} was created",
                user=employee,
            )
            
            # Success message
            return render(request, "add_employee.html", {
                'message': f'🎉 Employee {employee.name} added successfully!',
                'color': 'green'
            })
            
        except Exception as e:
            print(f"❌ Error adding employee: {str(e)}")
            return render(request, "add_employee.html", {
                'error': f'Error: {str(e)}',
                'color': 'red'
            })
    
    # GET request - show add employee form
    return render(request, "add_employee.html")


def update_employee(request, email):
    print("UPDATE SESSION ROLE:", request.session.get("role"))
    print("UPDATE SESSION NAME:", request.session.get("name"))
    print("UPDATE SESSION EMAIL:", request.session.get("email"))
    employee = Employee.objects.get(
    email=email,
    isDeleted=False
)

    if request.method == "POST":

        employee.name = request.POST["name"]
        employee.age = request.POST["age"]
        employee.email = request.POST["email"]
        employee.mobile = request.POST["mobile"]
        employee.department = request.POST["department"]
        employee.city = request.POST["city"]
        employee.joining_date = request.POST.get("joining_date")
        employee.salary = request.POST.get("salary")
        employee.address = request.POST.get("address")
        employee.department = request.POST.get("department")
        employee.password = request.POST["password"]
        employee.gender = request.POST.get("gender")
        employee.role = request.POST.get("role")
        employee.status = request.POST.get("status")
        employee.updatedBy = request.session.get("role")
        print("Updated By:", employee.updatedBy)

        employee.updated_date = timezone.now()
        employee.save()

        # Create UPDATE Activity Log
        log_activity(
            request=request,
            action="UPDATE",
            description=f"Employee {employee.name} was updated",
            user=employee,
        )

        return redirect("view_employee")

    return render(
        request,
        "update_employee.html",
        {
            "employee": employee
        }
    )



def delete_employee(request, email):
    employee = get_object_or_404(Employee, email=email)

    employee.isDeleted = True
    employee.status = "Inactive"

    print(employee.isDeleted)
    print(employee.status)

    employee.save()

    # Create DELETE Activity Log
    log_activity(
        request=request,
        action="DELETE",
        description=f"Employee {employee.name} was deleted",
        user=employee,
    )

    return redirect("view_employee")




def view_employee(request):

    employees = Employee.objects.filter(
        isDeleted=False
    )

    # ---------------- Search ----------------

    search = request.GET.get("search")

    if search:
        employees = employees.filter(
            name__icontains=search
        )

    # ---------------- Status Filter ----------------

    status = request.GET.get("status")

    if status == "Active":
        employees = employees.filter(
            status="Active"
        )

    elif status == "Inactive":
        employees = employees.filter(
            status="Inactive"
        )

    # ---------------- Role Filter ----------------

    role = request.GET.get("role")

    if role in ["Admin", "admin"]:
        employees = employees.filter(
            role="Admin"
        )

    elif role in ["User", "user"]:
        employees = employees.filter(
            role="User"
        )

    # ---------------- Sorting ----------------
    sort = request.GET.get("sort")

    print("SORT VALUE:", sort)

    if sort == "name":
        employees = employees.order_by("name")

    elif sort == "-name":
        employees = employees.order_by("-name")

    elif sort == "new":
        employees = employees.order_by("-created_date")

    elif sort == "old":
        employees = employees.order_by("created_date")

    elif sort == "salary_high":
        employees = employees.order_by("-salary")

    elif sort == "salary_low":
        employees = employees.order_by("salary")

    # ---------------- Pagination ----------------

    paginator = Paginator(employees, 8)

    page = request.GET.get("page")

    employees = paginator.get_page(page)

    return render(
        request,
        "view_employee.html",
        {
            "employees": employees,
        }
    )




def search(request):
    
    employees = Employee.objects.none()
    msg = ""

    if request.method == "POST":

        id = request.POST.get("id")
        name = request.POST.get("name")
        email = request.POST.get("email")
        department = request.POST.get("department")
        city = request.POST.get("city")
        gender = request.POST.get("gender")
        role = request.POST.get("role")

        if id:
            employees = Employee.objects.filter(id=id)

        elif name:
            employees = Employee.objects.filter(name__icontains=name)

        elif email:
            Employee.objects.filter(
    isDeleted=False,
    email=email
)
        
        elif gender:
            employees = Employee.objects.filter(gender__icontains=gender)
            if gender == "Male" or gender == "male":
                employees = Employee.objects.filter(gender__iexact="Male")
            elif gender == "Female" or gender == "female":
                employees = Employee.objects.filter(gender__iexact="Female")
            else:
                employees = Employee.objects.filter(gender__iexact="Other")

        elif role:
            employees = Employee.objects.filter(role__icontains=role)
            if role == "Admin" or role == "admin":
                employees = Employee.objects.filter(role__iexact="Admin")
            elif role == "User" or role == "user":
                employees = Employee.objects.filter(role__iexact="User")
            else:
                employees = Employee.objects.filter(role__iexact="Other")

        elif department:
            employees = Employee.objects.filter(department__icontains=department)

        elif city:
            employees = Employee.objects.filter(city__icontains=city)

        else:
            msg = "Please provide at least one search criteria."

        if not employees.exists():
            msg = "Employee not found!"

    return render(request, "search.html", {
        "employees": employees,
        "msg": msg
    })
#==========Give Page===============
def Givemesignuppage(request):
    return render(request,"signup.html")

def Givemehomepage(request):
    return render(request,"home.html")

def Givemeaddemployeepage(request):
    return render(request, "add_employee.html")

def Givemeupdateemployeepage(request):
    return render(request,"update_employee.html")

def Givemedeleteemployeepage(request):
    return render(request,"delete_employee.html")

def Givemeviewemployeepage(request):
    return redirect("view_employee.html")


def Givemesearchpage(request):
    return render(request,'search.html')

def Givemesigninpage(request):
    return render(request,'signin.html')

def Givemesignoutpage(request):
    return render(request, "signout.html")
###################################################################################################

def change_status(request, email):
    
    employee = Employee.objects.get(email=email)

    if employee.status == "Active":
        employee.status = "Inactive"
    else:
        employee.status = "Active"

    employee.save()

    return redirect("total_employees")


@user_required
@login_required
def user_dashboard(request):

    if "email" not in request.session:
        return redirect("signin")

    employee = Employee.objects.get(
        email=request.session["email"],
        isDeleted=False
    )

    total_employees = Employee.objects.filter(
        isDeleted=False
    ).count()

    active_employees = Employee.objects.filter(
        status="Active",
        isDeleted=False
    ).count()
    
    # Employees added today
    today = timezone.localdate()

    start = timezone.make_aware(
    dt.datetime.combine(today, dt.time.min)
)

    end = timezone.make_aware(
    dt.datetime.combine(today, dt.time.max)
)

    recent_employees = Employee.objects.filter(
    isDeleted=False,
    created_date__gte=start,
    created_date__lte=end
).count()

    print("Today:", today)
    print("Start:", start)
    print("End:", end)
    print("Recently Added Count:", recent_employees)


    department = Employee.objects.filter(
        role="User",
        isDeleted=False
    ).values("department").annotate(total=Count("department"))

    gender = Employee.objects.filter(
        role="User",
        isDeleted=False
    ).values("gender").annotate(total=Count("gender"))

    context = {
        "employee": employee,
        "total_employees": total_employees,
        "active_employees": active_employees,
        "recent_employees": recent_employees,
        "department": department,
        "gender": gender,
    }

    return render(request, "user_dashboard.html", context)




def create_admin(request):

    if request.method == "POST":

        name = request.POST["name"]
        age = request.POST["age"]
        email = request.POST["email"]
        mobile = request.POST["mobile"]
        department = request.POST["department"]
        city = request.POST["city"]
        password = request.POST["password"]


        admin = Employee.objects.create(

            name=name,
            age=age,
            email=email,
            mobile=mobile,
            department=department,
            city=city,
            password=make_password(password)

        )


        # Store newly created admin details in session
        request.session["admin_id"] = admin.id
        request.session["admin_name"] = admin.name
        request.session["admin_email"] = admin.email


        return redirect("dashboard")


    return render(request,"create_admin.html")




def profile(request):
    if "email" not in request.session:
        return redirect("signin")

    employee = Employee.objects.get(
    email=request.session["email"],
    isDeleted=False
)
    if employee.role == "Admin":
        return render(request, "admin_profile.html", {"employee": employee})

    return render(request, "profile.html", {"employee": employee})


def update_profile(request):

    if "email" not in request.session:
        return redirect("signin")

    employee = Employee.objects.get(email=request.session["email"])

    if request.method == "POST":

        employee.name = request.POST["name"]
        employee.age = request.POST["age"]
        employee.mobile = request.POST["mobile"]
        employee.department = request.POST["department"]
        employee.city = request.POST["city"]
        employee.gender = request.POST["gender"]
        employee.status = request.POST.get("status")
        employee.address = request.POST.get("address")
        employee.joining_date = request.POST.get("joining_date")
        employee.salary = request.POST.get("salary")
        employee.updatedBy = request.session.get("role")
        employee.createdBy = request.session.get("role")
        employee.created_date = timezone.now()

        # Update email if changed
        new_email = request.POST["email"]
        employee.email = new_email

        # Update session if email changes
        request.session["email"] = new_email
        
        if "profile_photo" in request.FILES:
            employee.profile_photo = request.FILES["profile_photo"]

        employee.save()

        return redirect("profile")

    return render(request, "update_profile.html", {
        "employee": employee
    })



def change_password(request):

    if "email" not in request.session:
        return redirect("signin")

    employee = Employee.objects.get(email=request.session["email"])

    if request.method == "POST":

        current_password = request.POST["current_password"]
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]

        # Check current password
        if not check_password(current_password, employee.password):
            return render(request, "change_password.html", {
                "message": "Current password is incorrect."
            })

        # Check new password and confirm password
        if new_password != confirm_password:
            return render(request, "change_password.html", {
                "message": "New password and Confirm Password do not match."
            })

        # Prevent using the same password
        if check_password(new_password, employee.password):
            return render(request, "change_password.html", {
                "message": "New password cannot be the same as the current password."
            })

        # Save encrypted password
        employee.password = make_password(new_password)
        employee.save()

        # Create Password Change Activity Log
        log_activity(
            request=request,
            action="PASSWORD_CHANGE",
            description=f"{employee.name} changed their password",
            user=employee,
        )

        return render(request, "change_password.html", {
            "success": "Password changed successfully."
        })

    return render(request, "change_password.html")



def forgot_password(request):
    
    if request.method == "POST":

        email = request.POST.get("email")

        try:
            employee = Employee.objects.get(email=email)

            otp = str(random.randint(100000, 999999))

            # Remove old OTP
            OTP.objects.filter(employee=employee).delete()

            # Create new OTP
            OTP.objects.create(
                employee=employee,
                otp=otp
            )

            send_mail(
                "Password Reset OTP",
                f"Your OTP is {otp}",
                "gayatridevghare5@gmail.com",
                [email],
                fail_silently=False
            )

            # Store email for next steps
            request.session["reset_email"] = email

            return redirect("verify_otp")

        except Employee.DoesNotExist:

            return render(
                request,
                "forgot_password.html",
                {
                    "message": "Email not registered."
                }
            )

    return render(request, "forgot_password.html")




def verify_otp(request):
    if "reset_email" not in request.session:
        return redirect("forgot_password")

    if request.method == "POST":

        entered_otp = request.POST.get("otp")

        email = request.session.get("reset_email")

        try:
            employee = Employee.objects.get(email=email)

            otp_record = OTP.objects.get(employee=employee)

            if otp_record.otp == entered_otp:

                messages.success(
                    request,
                    "OTP verified successfully"
                )

                # Mark OTP verification complete
                request.session["otp_verified"] = True

                # Remove OTP after successful verification
                otp_record.delete()

                return redirect("reset_password")

            else:

                messages.error(
                    request,
                    "Invalid OTP"
                )

        except Employee.DoesNotExist:

            messages.error(
                request,
                "User not found"
            )

        except OTP.DoesNotExist:

            messages.error(
                request,
                "OTP expired or not found"
            )

    return render(request, "verify_otp.html")




def reset_password(request):
    
    if not request.session.get("otp_verified"):
        messages.error(request, "Please verify OTP first.")
        return redirect("forgot_password")

    if request.method == "POST":

        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not password or not confirm_password:
            messages.error(request, "Please enter both passwords.")
            return redirect("reset_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password")

        if len(password) < 6:
            messages.error(
                request,
                "Password must be at least 6 characters long."
            )
            return redirect("reset_password")

        email = request.session.get("reset_email")

        try:
            employee = Employee.objects.get(
                email=email,
                isDeleted=False
            )

            # Check whether new password is same as old password
            if check_password(password, employee.password):
                messages.error(
                    request,
                    "New password cannot be the same as the old password."
                )
                return redirect("reset_password")

            # Hash new password
            employee.password = make_password(password)
            employee.save(update_fields=["password"])

            # Verify that the new password was actually saved correctly
            print("================================")
            print("PASSWORD RESET")
            print("Email:", employee.email)
            print("Password Hash:", employee.password)
            print(
                "Password Check:",
                check_password(password, employee.password)
            )
            print("================================")

            # Clear reset session
            request.session.pop("otp_verified", None)
            request.session.pop("reset_email", None)

            messages.success(
                request,
                "Password reset successfully. Please sign in."
            )

            return redirect("signin")

        except Employee.DoesNotExist:
            messages.error(
                request,
                "Employee not found."
            )
            return redirect("forgot_password")

    return render(request, "reset_password.html")



def remove_profile_photo(request):

    if "email" not in request.session:
        return redirect("signin")

    if request.method == "POST":

        try:
            employee = Employee.objects.get(
                email=request.session["email"]
            )

            if employee.profile_photo:
                employee.profile_photo.delete(save=False)  
                employee.profile_photo = None              
                employee.save()

        except Employee.DoesNotExist:
            pass

    return redirect("profile")




def change_profile_photo(request):

    if request.method == "POST":

        email = request.session.get("email")

        employee = Employee.objects.get(email=email)

        if "profile_photo" in request.FILES:

            employee.profile_photo = request.FILES["profile_photo"]
            employee.save()

            messages.success(request, "Profile photo updated successfully.")

        else:
            messages.error(request, "Please choose a photo.")

    return redirect("profile")



def edit_profile(request):
    if "email" not in request.session:
        return redirect("signin")

    employee = Employee.objects.get(email=request.session["email"])

    if request.method == "POST":

        employee.name = request.POST["name"]
        employee.age = request.POST["age"]
        employee.email = request.POST["email"]
        employee.department = request.POST["department"]
        employee.city = request.POST["city"]
        employee.status = request.POST.get("status")
        employee.gender = request.POST.get("gender")
        employee.mobile = request.POST["mobile"]
        employee.address = request.POST.get("address")

        employee.save()

        # Update session if email changes
        request.session["email"] = employee.email

        messages.success(request, "Profile updated successfully.")

        return redirect("profile")

    return render(request, "edit_profile.html", {"employee": employee})



def upload_photo(request):
    if "email" not in request.session:
        return redirect("signin")

    print("Session Email:", request.session["email"])

    employee = Employee.objects.get(email=request.session["email"])

    if request.method == "POST":
        print("FILES =", request.FILES)

        if "photo" in request.FILES:
            employee.profile_photo = request.FILES["photo"]
            employee.save()

            print("Saved Photo =", employee.profile_photo)

            return redirect("profile")

    return render(request, "upload_photo.html", {"employee": employee})



@admin_required
@login_required
def activity_logs_page(request):
    employees = Employee.objects.filter(
        isDeleted=False
    ).order_by("-created_date")

    paginator = Paginator(employees,8)

    page = request.GET.get("page")
    employees = paginator.get_page(page)

    return render(
        request,
        "activity_log.html",
        {
            "employees": employees
        }
    )