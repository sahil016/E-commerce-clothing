"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from myapp1 import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home', views.home, name='home'),
    path('index/', views.index, name='index'),  # This will map the home view to the root URL
    path('about', views.about, name='about'),
    path('cpass', views.cpass, name='cpass'),
    path('signup', views.signup, name='signup'),
    path('login' ,views.login, name='login'),
    path('logout' ,views.logout, name='logout'),
    path('fpass' ,views.fpass, name='fpass'),
    path('otp' ,views.otp, name='otp'),
    path('newpass' ,views.newpass, name='newpass'),
    path('cprofile' ,views.cprofile, name='cprofile'),
    path('sindex' ,views.sindex, name='sindex'),
    path('scpass' ,views.scpass, name='scpass'),
    path('scprofile' ,views.scprofile, name='scprofile'),
    path('add' ,views.add, name='add'),
    path('view' ,views.view, name='view'),
    path('update/<int:pk>' ,views.update, name='update'),
    path('delete/<int:pk>' ,views.delete, name='delete'),
    path('shop' ,views.shop, name='shop'),
    path('wishlist' ,views.wishlist, name='wishlist'),
    path('addwish/<int:pk>' ,views.addwish, name='addwish'),

    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),  # Add this
    path('detail/<int:pk>' ,views.details, name='details'),
    path('dwishlist/<int:pk>',views.dwishlist,name='dwishlist' ),
    path('cart',views.cart,name='cart'),
    path('sucess',views.sucess,name='sucess'),

    path('del_cart/<int:pk>/', views.del_cart, name='del_cart'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

