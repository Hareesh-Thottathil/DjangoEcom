from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CheckoutForm, CustomAuthenticationForm, ProductForm, SellerProfileForm, UsersForm
from .models import Category, Order, OrderItem, Product, SellerProfile


def get_cart_data(request):
    cart = request.session.get('cart', {})
    items = []
    total = Decimal('0.00')

    for product_id, item_data in cart.items():
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            continue
        quantity = int(item_data.get('quantity', 1))
        if quantity > product.stock:
            quantity = product.stock
        if quantity < 1:
            continue
        line_total = product.price * quantity
        items.append({
            'product': product,
            'quantity': quantity,
            'line_total': line_total,
        })
        total += line_total

    return {'items': items, 'total': total, 'count': sum(item['quantity'] for item in items)}


def home(request):
    category_slug = request.GET.get('category')
    products = Product.objects.filter(stock__gt=0).order_by('-created_at')
    categories = Category.objects.all()
    if category_slug:
        products = products.filter(category__slug=category_slug)
    return render(request, 'home.html', {'products': products, 'categories': categories, 'cart': get_cart_data(request)})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'product_detail.html', {'product': product, 'cart': get_cart_data(request)})


@login_required
def add_to_cart(request, product_id):
    if getattr(request.user, 'role', None) == 'seller':
        messages.error(request, 'Sellers cannot place orders.')
        return redirect('home')

    product = get_object_or_404(Product, pk=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        messages.error(request, 'Please choose a valid quantity.')
        return redirect('product_detail', slug=product.slug)

    if quantity > product.stock:
        messages.error(request, 'Only a limited number of items are available in stock.')
        return redirect('product_detail', slug=product.slug)

    cart = request.session.get('cart', {})
    existing_quantity = int(cart.get(str(product_id), {}).get('quantity', 0))
    new_quantity = existing_quantity + quantity
    if new_quantity > product.stock:
        new_quantity = product.stock

    cart[str(product_id)] = {'quantity': new_quantity}
    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, f'{product.name} was added to your cart.')
    return redirect('cart')


def cart_view(request):
    return render(request, 'cart.html', {'cart': get_cart_data(request)})


@login_required
def update_cart(request, product_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        product = get_object_or_404(Product, pk=product_id)

        if quantity <= 0:
            cart.pop(str(product_id), None)
        else:
            cart[str(product_id)] = {'quantity': min(quantity, product.stock)}

        request.session['cart'] = cart
        request.session.modified = True
        messages.info(request, 'Your cart was updated.')
    return redirect('cart')


@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    request.session.modified = True
    messages.info(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
def checkout(request):
    if getattr(request.user, 'role', None) == 'seller':
        messages.error(request, 'Sellers cannot place orders.')
        return redirect('home')

    cart = get_cart_data(request)
    if not cart['items']:
        messages.info(request, 'Your cart is empty.')
        return redirect('home')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                phone=form.cleaned_data['phone'],
                total_price=cart['total'],
            )
            for item in cart['items']:
                product = item['product']
                quantity = item['quantity']
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price_at_purchase=product.price,
                )
                product.stock = max(0, product.stock - quantity)
                product.save(update_fields=['stock'])

            request.session['cart'] = {}
            request.session.modified = True
            messages.success(request, 'Your order has been placed successfully.')
            return redirect('order_history')
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {'form': form, 'cart': cart})


@login_required
def order_history(request):
    orders = request.user.orders.order_by('-created_at')
    return render(request, 'orders.html', {'orders': orders, 'cart': get_cart_data(request)})


@login_required
def add_product(request):
    if not getattr(request.user, 'role', None) == 'seller':
        messages.error(request, 'Only sellers can add products.')
        return redirect('home')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            messages.success(request, 'Product added successfully.')
            return redirect('home')
    else:
        form = ProductForm()

    return render(request, 'add_product.html', {'form': form, 'cart': get_cart_data(request)})


class RegisterView(CreateView):
    form_class = UsersForm
    template_name = 'register.html'
    success_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.request.POST.get('role', 'buyer')
        context['seller_form'] = SellerProfileForm(self.request.POST or None)
        return context

    def form_valid(self, form):
        try:
            user = form.save()
        except IntegrityError as e:
            if 'username' in str(e):
                form.add_error('username', 'This username is already taken. Please choose another one.')
            elif 'email' in str(e):
                form.add_error('email', 'This email is already registered.')
            else:
                form.add_error(None, 'An error occurred during registration. Please try again.')
            return self.render_to_response(self.get_context_data(form=form))

        if user.role == 'seller':
            seller_form = SellerProfileForm(self.request.POST)
            seller_form.fields['shop_name'].required = True
            if seller_form.is_valid():
                seller = seller_form.save(commit=False)
                seller.user = user
                seller.save()
            else:
                user.delete()
                return self.render_to_response(self.get_context_data(form=form, seller_form=seller_form))

        messages.success(self.request, 'User account created successfully. You can now log in.')
        return redirect('login')


class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = CustomAuthenticationForm

    def form_valid(self, form):
        login_role = self.request.POST.get('login_role')
        user = form.get_user()
        if login_role and user.role != login_role:
            form.add_error(None, 'Selected role does not match this account.')
            return self.form_invalid(form)
        messages.success(self.request, 'You have successfully logged in.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Login'
        return context


def custom_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')
