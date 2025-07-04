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
from webapp.views import (index, aboutus, FAQ, helper, profile, set_default_address, set_default_card, delivery, news,
                          gift, catalog, contact, logout_view,
                          register, update_order_status, panel_admina, cancel_order)
from django.contrib.auth import views as auth_views

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('', index, name='main'),
                  path('aboutus/', aboutus, name='about'),
                  path('FAQ/', FAQ, name='FAQ'),
                  path('category/<int:category_id>/', views.product_list_by_category, name='product_list_by_category'),
                  path('helper/', helper, name='helper'),
                  path('profile/', profile, name='profile'),
                  path('delivery/', delivery, name='delivery'),
                  path('news/', news, name='news'),
                  path('gift/', gift, name='gift'),
                  path('contact/', contact, name='contact'),
                  path('product/<int:pk>/', views.product_view, name='product_view'),
                  path('logout_view', logout_view, name='logout_view'),
                  path("login/", auth_views.LoginView.as_view(template_name='login.html'), name='login'),
                  path('register/', register, name='register'),
                  path('catalog/', catalog, name='catalog'),
                  path('profile/address/<int:address_id>/default/', views.set_default_address,
                       name='set_default_address'),
                  path('profile/card/<int:card_id>/default/', views.set_default_card, name='set_default_card'),
                  path('profile/address/<int:address_id>/delete/', views.delete_address, name='delete_address'),
                  path('profile/card/<int:card_id>/delete/', views.delete_card, name='delete_card'),
                  path('cart/', views.view_cart, name='view_cart'),
                  path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
                  path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
                  path('cart/update/<int:product_id>/', views.update_cart_item, name='update_cart_item'),
                  path('checkout/', views.checkout, name='checkout'),
                  path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
                  path('orders/', views.order_history, name='order_history'),
                  path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
                  path('check-cart/', views.check_cart, name='check_cart'),
                  path('wishlist/count/', views.wishlist_count, name='wishlist_count'),
                  path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
                  path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
                  path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
                  path('wishlist/', views.view_wishlist, name='view_wishlist'),
                  path('admin-panel/', views.panel_admina, name='panel_admina'),
                  path('admin-panel/update-status/<int:order_id>/<str:new_status>/',
                       views.update_order_status, name='update_order_status'),
                  path('admin-panel/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
