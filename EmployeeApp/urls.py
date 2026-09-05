from django.urls import path
from . import views, api_views
from .api_views import (signup_api,activity_logs_api,activity_logs_export_csv)
from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView,)

urlpatterns = [
#=======curd page========
path("", views.signin, name="signin"),
path("signup/", views.signup, name="signup"),
path("dashboard/", views.dashboard, name="dashboard"),
path("activity-log/",views.activity_logs_page,name="activity_log"),
path("signout/", views.signout, name="signout"),
path("user_dashboard/", views.user_dashboard, name="user_dashboard"),
path("signin/", views.signin, name="signin"),

path('add_employee/',views.add_employee,name='add_employee'),
path("update_employee/<str:email>/", views.update_employee, name="update_employee"),

path("view_employee/", views.view_employee, name='view_employee'),
path("search/",views.search,name='search'),



#======== Give page=====
path('givemeaddemployee/',views.Givemeaddemployeepage),
path('givemeupdateemployee/',views.Givemeupdateemployeepage),
path('givemedeleteemployee/',views.Givemedeleteemployeepage),
path('givemeviewemployee/',views.Givemeviewemployeepage),
path('givemesearch/',views.Givemesearchpage),
path("givemesignup/", views.Givemesignuppage),
path('givemesignin/',views.Givemesigninpage),
path('givemesignout/',views.Givemesignoutpage),


# path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
path("api/activity-logs/",api_views.activity_logs_api,name="activity_logs_api"),
path("api/activity-logs/export/",api_views.activity_logs_export_csv,name="activity_logs_export_csv"),
path("api/signup/",api_views.signup_api),
path("api/signin/",api_views.signin_api),
path("api/signout/",api_views.signout_api),
path("api/add/",api_views.add_employee_api),
path("api/employees/",api_views.get_all_employee_api),
path("api/get_employee/<str:email>/",api_views.get_employee_api,name="get_employee_api"),
path("api/dashboard/", api_views.dashboard_api, name="dashboard_api"),
path("api/delete_employee/<str:email>/",api_views.delete_employee_api,name="delete_employee_api"),
path("api/update_user/<str:email>/", api_views.update_user, name="update_user"),
path("api/delete_user/<str:email>/", api_views.delete_user, name="delete_user"),



path("delete_employee/<str:email>/", views.delete_employee, name="delete_employee"),

path("change_status/<str:email>/",views.change_status,name="change_status"),

path("total_employees/",views.total_employees,name="total_employees"),

path("active_employees/",views.active_employees,name="active_employees"),

path("recent_employees/",views.recent_employees,name="recent_employees"),

path("create_admin/",views.create_admin,name="create_admin"),

path("profile/", views.profile, name="profile"),

path("update-profile/", views.update_profile, name="update_profile"),

path("change-password/", views.change_password, name="change_password"),

path("edit-profile/", views.edit_profile, name="edit_profile"),

path("forgot-password/", views.forgot_password, name="forgot_password"),

path("verify-otp/", views.verify_otp, name="verify_otp"),

path("reset-password/", views.reset_password, name="reset_password"),

path("remove-profile-photo/",views.remove_profile_photo,name="remove_profile_photo"),

path("upload-photo/", views.upload_photo, name="upload_photo"),

path("change_profile_photo/",views.change_profile_photo,name="change_profile_photo"),

]