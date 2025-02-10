from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Check if the user is newly created or modified without the STUDENT group
        student_group, created = Group.objects.get_or_create(name='STUDENT')
        if not change:  # If it's a new user
            obj.groups.add(student_group)

# Unregister the default User admin
admin.site.unregister(User)
# Register the User with the customized admin
admin.site.register(User, CustomUserAdmin)
