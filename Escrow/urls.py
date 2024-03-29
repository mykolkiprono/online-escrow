from django.contrib import admin
from django.urls import path
from Main.views import *

urlpatterns = [
     path('oauth_success/', oauth_success, name='oauth_success'),
    path('stk_push_success/', stk_push_success, name='stk_push_success'),
    # path('mpesa/', include(mpesa_urls)),
    
    path('admin/', admin.site.urls),
    path('', landing_view),
    path('home/', customer_view, name="customer-home"),
    path('signin/', signin, name="signin"),
    path('signup/', signup, name="signup"),
    path('search/', search, name="search"),
    path('payment<str:pk>/', payment, name="payment"),
    # path('commitment-fee', commitment_fee, name="commitment-fee"),
    path('send-complaint/<str:pk>/', send_complaint, name="send-complaint"),
    path('send-review/', send_review, name="send-review"),
    # path('payment/', payment, name="payment"),
    path('commitment_fee/<str:pk>', commitment_fee, name="commitment_fee"),
    path('reject-tansaction/<str:pk>/', reject_tansaction, name="reject-tansaction"),
    path('confirm-delivery/<str:pk>/', confirm_delivery, name="confirm-delivery"),

    path('intermediary/', intermediary_view, name="intermediary"),
    path('complaints/', complaints_view, name="complaints"),
    path('respond-complaint/<str:pk>/', respond_complaint, name="respond-complaint"),



    path('logout/', logout_view, name="logout"),
]
