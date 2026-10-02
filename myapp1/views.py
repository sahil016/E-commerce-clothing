import hmac
import secrets
import time
from functools import wraps

import razorpay
from django.conf import settings
from django.db import transaction
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .models import Cart, Product, User, Wishlist

OTP_VALID_SECONDS = 300  # 5 minutes


# ---------------------------------------------------------------- helpers
def login_required_session(view):
    """Redirect to login unless a valid user is in the session."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        email = request.session.get('email')
        if not email:
            return redirect('login')
        user = User.objects.filter(email=email).first()
        if user is None:
            request.session.flush()
            return redirect('login')
        request.current_user = user
        return view(request, *args, **kwargs)
    return wrapper


def seller_required(view):
    """Only sellers may use the wrapped view (must sit under login_required_session)."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.current_user.usertype == 'buyer':
            return redirect('index')
        return view(request, *args, **kwargs)
    return login_required_session(wrapper)


def verify_password(user, raw):
    """Check a password. Also upgrades old plain-text passwords to hashes on first use."""
    if check_password(raw, user.password):
        return True
    if user.password and hmac.compare_digest(user.password.encode(), raw.encode()):
        user.password = make_password(raw)
        user.save(update_fields=['password'])
        return True
    return False


def home_for(user):
    return 'index' if user.usertype == 'buyer' else 'sindex'


# ---------------------------------------------------------------- public pages
def home(request):
    return render(request, 'home.html')


def index(request):
    products = Product.objects.all()
    return render(request, 'index.html', {'products': products})


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


# ---------------------------------------------------------------- auth
def signup(request):
    if request.method != "POST":
        return render(request, 'signup.html')

    email = (request.POST.get('email') or '').strip().lower()
    mobile = (request.POST.get('mobile') or '').strip()
    password = request.POST.get('password') or ''
    usertype = request.POST.get('usertype')

    if usertype not in ('buyer', 'seller'):
        return render(request, 'signup.html', {'msg': "Invalid user type"})
    if User.objects.filter(email=email).exists():
        return render(request, 'signup.html', {'msg': "Email already exists!!"})
    if User.objects.filter(mobile=mobile).exists():
        return render(request, 'signup.html', {'msg': "Mobile number already exists!!"})
    if not password or password != request.POST.get('cpassword'):
        return render(request, 'signup.html', {'msg': "Password & confirm password do not match"})

    User.objects.create(
        usertype=usertype,
        name=request.POST.get('name'),
        email=email,
        mobile=mobile,
        password=make_password(password),
        profile=request.FILES.get('profile'),
    )
    return render(request, 'login.html', {'msg': "Signup Successfully"})


def login(request):
    if request.method != "POST":
        return render(request, 'login.html')

    email = (request.POST.get('email') or '').strip().lower()
    password = request.POST.get('password') or ''

    user = User.objects.filter(email=email).first()
    if user is None:
        return render(request, 'login.html', {'msg': "Invalid Email!!"})
    if not verify_password(user, password):
        return render(request, 'login.html', {'msg': "Invalid Password!!"})

    request.session['email'] = user.email
    request.session['profile'] = user.profile.url if user.profile else ''
    return redirect(home_for(user))


def logout(request):
    request.session.flush()
    return redirect('login')


@login_required_session
def cpass(request):
    user = request.current_user
    template = 'cpass.html' if user.usertype == 'buyer' else 'scpass.html'

    if request.method != "POST":
        return render(request, template)

    new = request.POST.get('npassword') or ''
    if not verify_password(user, request.POST.get('opassword') or ''):
        msg = "Old Password does not match"
    elif not new or new != request.POST.get('cnpassword'):
        msg = "Password & confirm password do not match"
    else:
        user.password = make_password(new)
        user.save(update_fields=['password'])
        return redirect('logout')
    return render(request, template, {'msg': msg})


# ---------------------------------------------------------------- forgot password (email OTP)
def fpass(request):
    if request.method != "POST":
        return render(request, 'fpass.html')

    email = (request.POST.get('email') or '').strip().lower()
    user = User.objects.filter(email=email).first()
    if user is None:
        return render(request, 'fpass.html', {'msg': "Email not found!!"})

    otp = secrets.randbelow(9000) + 1000  # 1000-9999
    try:
        send_mail(
            subject="Your password reset OTP",
            message=f"Your OTP is {otp}. It is valid for 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        print("Email error:", type(e).__name__, e)
        if settings.DEBUG:
            print("DEV MODE, OTP is:", otp)        # keep testing if email fails
        else:
            return render(request, 'fpass.html', {'msg': "Could not send OTP. Try again."})

    request.session['reset_email'] = user.email
    request.session['otp'] = str(otp)
    request.session['otp_time'] = time.time()
    request.session['otp_verified'] = False
    return render(request, 'otp.html')


def otp(request):
    if request.method != "POST":
        return render(request, 'otp.html')

    saved = request.session.get('otp')
    if not saved:
        return redirect('fpass')

    if time.time() - request.session.get('otp_time', 0) > OTP_VALID_SECONDS:
        for key in ('otp', 'otp_time'):
            request.session.pop(key, None)
        return render(request, 'fpass.html', {'msg': "OTP expired. Request a new one."})

    entered = (request.POST.get('uotp') or '').strip()
    if hmac.compare_digest(str(saved), entered):
        request.session.pop('otp', None)
        request.session.pop('otp_time', None)
        request.session['otp_verified'] = True
        return render(request, 'newpass.html')
    return render(request, 'otp.html', {'msg': "Invalid OTP!!"})


def newpass(request):
    # Only reachable after a successful OTP check
    if not (request.session.get('reset_email') and request.session.get('otp_verified')):
        return redirect('fpass')

    if request.method != "POST":
        return render(request, 'newpass.html')

    new = request.POST.get('npassword') or ''
    if not new or new != request.POST.get('cnpassword'):
        return render(request, 'newpass.html',
                      {'msg': "New password & confirm new password do not match!!"})

    user = User.objects.filter(email=request.session['reset_email']).first()
    if user is None:
        return render(request, 'newpass.html', {'msg': "User does not exist or session expired."})

    user.password = make_password(new)
    user.save(update_fields=['password'])
    for key in ('reset_email', 'otp_verified'):
        request.session.pop(key, None)
    return redirect('login')


# ---------------------------------------------------------------- profile
@login_required_session
def cprofile(request):
    user = request.current_user
    template = 'cprofile.html' if user.usertype == 'buyer' else 'scprofile.html'

    if request.method != "POST":
        return render(request, template, {'user': user})

    mobile = (request.POST.get('mobile') or '').strip()
    if User.objects.filter(mobile=mobile).exclude(pk=user.pk).exists():
        return render(request, template, {'user': user, 'msg': "Mobile number already exists!!"})

    user.name = request.POST.get('name')
    user.mobile = mobile
    if request.FILES.get('profile'):      # photo is optional
        user.profile = request.FILES['profile']
    user.save()
    request.session['profile'] = user.profile.url if user.profile else ''
    return redirect(home_for(user))


@login_required_session
def scpass(request):
    return cpass(request)


@login_required_session
def scprofile(request):
    return cprofile(request)


# ---------------------------------------------------------------- seller
@seller_required
def sindex(request):
    return render(request, 'sindex.html')


@seller_required
def add(request):
    if request.method != "POST":
        return render(request, 'add.html')
    try:
        Product.objects.create(
            seller=request.current_user,
            pname=request.POST['pname'],
            scategory=request.POST['scategory'],
            sbrand=request.POST['sbrand'],
            ssize=request.POST['ssize'],
            price=request.POST['price'],
            description=request.POST['description'],
            image=request.FILES['image'],
        )
    except Exception as e:
        print("add product error:", e)
        return render(request, 'add.html', {'msg': "Could not add product. Check all fields."})
    return render(request, 'add.html', {'msg': "Product added successfully!!"})


@seller_required
def view(request):
    product = Product.objects.filter(seller=request.current_user)
    return render(request, 'view.html', {'product': product})


@seller_required
def update(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.current_user)

    if request.method == 'POST':
        # fields use the same names as in add(); keep old value if a field is missing
        for field, key in (('pname', 'pname'), ('scategory', 'scategory'), ('sbrand', 'sbrand'),
                           ('ssize', 'ssize'), ('price', 'price'), ('description', 'description')):
            value = request.POST.get(key)
            if value not in (None, ''):
                setattr(product, field, value)
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        product.save()
        return redirect('update', pk=product.pk)

    return render(request, 'update.html', {'product': product})


@seller_required
def delete(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.current_user)
    product.delete()
    return redirect('view')


# ---------------------------------------------------------------- shop
def shop(request):
    products = Product.objects.all()
    return render(request, 'shop.html', {'products': products})


def details(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product-single.html', {'product': product})


# ---------------------------------------------------------------- wishlist
@login_required_session
def addwish(request, pk):
    product = get_object_or_404(Product, pk=pk)
    Wishlist.objects.get_or_create(user=request.current_user, product=product)
    return redirect('wishlist')


@login_required_session
def wishlist(request):
    items = Wishlist.objects.filter(user=request.current_user)
    return render(request, 'wishlist.html', {'wishlist': items})


@login_required_session
def dwishlist(request, pk):
    item = get_object_or_404(Wishlist, pk=pk, user=request.current_user)
    item.delete()
    return redirect('wishlist')


# ---------------------------------------------------------------- cart & payment
@login_required_session
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    item, created = Cart.objects.get_or_create(
        user=request.current_user, product=product, payment=False,
        defaults={'price': product.price, 'qty': 1},
    )
    if not created:
        item.qty += 1
        item.save()
    return redirect('shop')


@login_required_session
def cart(request):
    cart_items = Cart.objects.filter(user=request.current_user, payment=False)
    total_price = sum(i.product.price * i.qty for i in cart_items)

    payment = None
    if total_price > 0:
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            payment = client.order.create({
                'amount': int(round(total_price * 100)),  # paise, must be an integer
                'currency': 'INR',
                'payment_capture': 1,
            })
            # tag these items with the order so the callback can find them
            cart_items.update(razorpay_order_id=payment['id'])
        except Exception as e:
            print("Razorpay order error:", e)

    return render(request, 'cart.html', {
        'cart': cart_items,
        'total_price': total_price,
        'payment': payment,
    })


@login_required_session
def del_cart(request, pk):
    item = get_object_or_404(Cart, pk=pk, user=request.current_user)
    item.delete()
    return redirect('cart')


@csrf_exempt
def sucess(request):
    # No login required: the session cookie may be missing on a cross-site
    # callback. The signature + order id identify the payment instead.
    data = request.POST if request.method == "POST" else request.GET
    params = {
        'razorpay_order_id': data.get('razorpay_order_id', ''),
        'razorpay_payment_id': data.get('razorpay_payment_id', ''),
        'razorpay_signature': data.get('razorpay_signature', ''),
    }
    if not all(params.values()):
        return redirect('cart')

    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        client.utility.verify_payment_signature(params)      # raises if fake/tampered
        order = client.order.fetch(params['razorpay_order_id'])
    except Exception as e:
        print("Payment verification failed:", e)
        return redirect('cart')

    with transaction.atomic():
        items = list(
            Cart.objects.select_for_update()
            .select_related('product')
            .filter(razorpay_order_id=params['razorpay_order_id'], payment=False)
        )
        if items:   # empty on page refresh: already processed
            total = sum(i.product.price * i.qty for i in items)
            if int(round(total * 100)) != order['amount']:
                print("Amount mismatch for order", params['razorpay_order_id'])
                return redirect('cart')
            Cart.objects.filter(pk__in=[i.pk for i in items]).update(payment=True)

    return render(request, 'secess.html', {'cart_items': items})