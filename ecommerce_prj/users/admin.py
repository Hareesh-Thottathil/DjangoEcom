from django.contrib import admin

from .models import Order, OrderItem, Product, SellerProfile, User, Category

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'stock', 'category', 'seller', 'created_at')
    list_filter = ('category', 'seller', 'created_at')
    search_fields = ('name', 'description')

    prepopulated_fields = {
        'slug': ('name',)
    }

    list_per_page = 20

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)

    prepopulated_fields = {
        'slug': ('name',)
    }

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'mobile')
    list_filter = ('role',)
    search_fields = ('username','email','mobile')

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop_name', 'user','gst_number')
    search_fields = ('shop_name', 'user__username')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status','created_at')
    search_fields = ('user__username','full_name','phone')
    readonly_fields = ('created_at',)

    inlines = [OrderItemInline]

admin.site.site_header = "ShopHub Administration"
admin.site.site_title = "ShopHub Admin"
admin.site.index_title = "Welcome to ShopHub Dashboard"