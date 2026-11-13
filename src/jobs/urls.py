from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from jobs import views_web
from jobs.views import TaskViewSet

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("login/", views_web.login_page, name="login-page"),
    path("sign_up/", views_web.register_page, name="register-page"),
    path("tasks-ui/", views_web.task_list_page, name="task-list-page"),
    path("tasks-ui/new/", views_web.task_form_page, name="task-form-page"),


    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include(router.urls)),
]