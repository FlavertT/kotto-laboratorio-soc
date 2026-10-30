from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from soc.views import experiment_report
urlpatterns = [path("experiments/<int:pk>/report/", experiment_report, name="experiment-report"), path("", RedirectView.as_view(url="/admin/", permanent=False)), path("admin/", admin.site.urls)]
