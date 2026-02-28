from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path

from library.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include('library.urls')),
]
