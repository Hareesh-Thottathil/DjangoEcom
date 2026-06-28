from django.contrib import admin

from .models import Order, OrderItem, Product, SellerProfile, User

admin.site.register(User)
admin.site.register(SellerProfile)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
