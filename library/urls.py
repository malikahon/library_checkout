from django.urls import path

from . import views

app_name = 'library'

urlpatterns = [
    path('', views.book_list_view, name='book_list'),
    path('books/<int:pk>/', views.book_detail_view, name='book_detail'),
    path('books/<int:pk>/checkout/', views.book_checkout_view, name='book_checkout'),
    path('loans/<int:pk>/return/', views.loan_return_view, name='loan_return'),
    path('my-loans/', views.my_loans_view, name='my_loans'),
    path('register/', views.register_view, name='register'),
]
