from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

from core import models

admin.site.register(models.Order)
admin.site.register(models.Product)
admin.site.register(models.Company)
admin.site.register(models.ShoppingCart)
admin.site.register(models.OrderProduct)
admin.site.register(models.OrderDetail)
admin.site.register(models.ProductCompany)
admin.site.register(models.OrderExecution)
admin.site.register(models.OrderProposalTemp)
admin.site.register(models.ProductCharacteristics)
admin.site.register(models.OrderExecutionProposal)


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = models.User
        fields = (
            'first_name', 'last_name', 'email', 'phone_number', 'company_name',
            'password1', 'password2', 'is_receiving_news', 'is_company'
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = models.User
        fields = (
            'first_name', 'last_name', 'email', 'phone_number',
            'company_name', 'password', 'is_active', 'is_admin'
        )


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('email',)}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'company_name')}),
        ('Permissions', {'fields': ('is_admin', 'is_active', 'is_company')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'first_name', 'last_name', 'email', 'phone_number',
                'company_name', 'password1', 'password2', 'is_receiving_news', 'is_company'
            ),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


admin.site.register(models.User, UserAdmin)
admin.site.unregister(Group)
