from django.contrib import admin
from .models import CallRequest


class CallRequestAdmin(admin.ModelAdmin):
    pass

admin.site.register(CallRequest, CallRequestAdmin)