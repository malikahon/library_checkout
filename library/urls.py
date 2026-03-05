from django.urls import path

from . import views

app_name = 'library'

urlpatterns = [
    # member URLs
    path('', views.book_list_view, name='book_list'),
    path('books/<int:pk>/', views.book_detail_view, name='book_detail'),
    path('books/<int:pk>/checkout/', views.book_checkout_view, name='book_checkout'),
    path('loans/<int:pk>/return/', views.loan_return_view, name='loan_return'),
    path('my-loans/', views.my_loans_view, name='my_loans'),
    path('register/', views.register_view, name='register'),

    # staff URLs books
    path('staff/books/', views.StaffBookListView.as_view(), name='staff_book_list'),
    path('staff/books/add/', views.StaffBookCreateView.as_view(), name='staff_book_add'),
    path('staff/books/<int:pk>/edit/', views.StaffBookUpdateView.as_view(), name='staff_book_edit'),
    path('staff/books/<int:pk>/delete/', views.StaffBookDeleteView.as_view(), name='staff_book_delete'),

    # staff URLs loans
    path('staff/loans/', views.StaffLoanListView.as_view(), name='staff_loan_list'),
    path('staff/loans/assign/', views.StaffLoanAssignView.as_view(), name='staff_loan_assign'),
    path('staff/loans/<int:pk>/force-return/', views.StaffForceReturnView.as_view(), name='staff_loan_force_return'),

    # staff URLs users
    path('staff/users/', views.StaffUserListView.as_view(), name='staff_user_list'),
]
