from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, Project, Task, Comment, Attachment, Notification

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')

admin.site.register(User, UserAdmin)
admin.site.register(Profile)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Comment)
admin.site.register(Attachment)
admin.site.register(Notification)
