from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import Product, SellerProfile


class UsersForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password1', 'password2', 'role', 'mobile', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'role' in self.fields:
            self.fields['role'].initial = 'buyer'


class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = ['shop_name', 'gst_number', 'business_address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional by default; validation will handle requirement
        for field_name in self.fields:
            self.fields[field_name].required = False


class CustomAuthenticationForm(AuthenticationForm):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    )
    login_role = forms.ChoiceField(choices=ROLE_CHOICES, initial='buyer', required=True)


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=200)
    address = forms.CharField(widget=forms.Textarea)
    city = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=20)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image', 'category']
