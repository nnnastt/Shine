"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from webapp import views
from webapp.views import index, aboutus, FAQ, helper, profile, delivery, news, gift, contact, logout_view
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',index,name='main'),
    path('aboutus/',aboutus,name='about'),
    path('FAQ/',FAQ,name='FAQ'),
    path('category/<int:category_id>/', views.product_list_by_category, name='product_list_by_category'),
    path('helper/',helper,name='helper'),
    path('profile/',profile,name='profile'),
    path('delivery/',delivery,name='delivery'),
    path('news/',news,name='news'),
    path('gift/',gift,name='gift'),
    path('contact/',contact,name='contact'),
    path('product/<int:pk>/', views.product_view, name='product_view'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('logout_view', logout_view, name='logout_view'),
    path("login/", auth_views.LoginView.as_view(template_name='login.html'),name='login'),



]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
