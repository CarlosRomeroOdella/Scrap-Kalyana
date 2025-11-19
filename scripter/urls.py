from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # cookies
    path("cookies/save", views.save_cookie, name="save_cookie"),
    # orders
    path("orders/year", views.orders_year, name="orders_year"),
    path("orders/range", views.orders_range, name="orders_range"),
    path("orders/all", views.orders_all_since, name="orders_all_since"),
    path("orders/export.csv", views.export_csv, name="export_csv_buffer"),
    # commissions (listado 21)
    path("commissions/month", views.commissions_month, name="commissions_month"),
    path("commissions/all", views.commissions_all_from, name="commissions_all_from"),
    # health
    path("health", views.health, name="health"),
]
