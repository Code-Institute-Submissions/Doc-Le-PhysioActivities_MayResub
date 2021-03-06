from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from user import views as UserViews

urlpatterns = [
    path('', include('home.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('user/', include('user.urls'), name='user'),
    path('login/', UserViews.login_form, name='login'),
    path('logout/', UserViews.logout_func, name='logout'),
    path('signup/', UserViews.signup_form, name='signup'),
    path('services/', include('services.urls'), name='services'),
    path('bookings/', include('bookings.urls'), name='bookings'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
