from django.shortcuts import render,redirect,get_object_or_404
from .models import *
from django.contrib import messages
import random
import requests
import razorpay
from django.conf import settings
from django.http import JsonResponse,HttpResponse
from django.shortcuts import render, redirect
from .models import User

# Create your views here.
def home(request):
    return render(request,'home.html')

def index(request):
    products = Product.objects.all()  
    return render(request,'index.html',{'products':products})




def cpass(request):
    user = User.objects.get(email=request.session['email'])
    if request.method == "POST":
        try:

            

           
            if user.password == request.POST['opassword']:
               
                if request.POST['npassword'] == request.POST['cnpassword']:
                    user.password = request.POST['npassword']
                    user.save()
                    return redirect('logout')  
                else:
                
                    msg = "Password & confirm password do not match"
                    if user.usertype=="buyer":
                        return render(request,'cpass.html', {'msg': msg})
                    else:
                        return render(request, 'scpass.html', {'msg': msg})

            else:
                
                msg = "Old Password does not match"
                if user.usertype=="buyer":
                    return render(request, 'cpass.html', {'msg': msg})
                else:
                    return render(request, 'scpass.html', {'msg': msg})
                    
       
        except Exception as e:
            
            print("*************",e)
            
            return render(request, 'cpass.html')

    else:
        if user.usertype=="buyer":
            return render(request, 'cpass.html')
        else:
            return render(request, 'scpass.html')


def about(request):
    return render(request, 'about.html')

 
def contact(request):
    return render(request, 'contact.html')

def signup(request):
    if request.method=="POST":
        try:
            user = User.objects.get(email=request.POST['email'])
            msg = "Email already exists!!"
            return render(request,'signup.html',{'msg':msg})
        except:
            if request.POST['password']==request.POST['password']:
                User.objects.create(
                    usertype=request.POST['usertype'],  
                    name = request.POST['name'],
                    email = request.POST['email'],
                    mobile = request.POST['mobile'],
                    password = request.POST['password'],
                    profile = request.FILES['profile']
                )

                msg = "Signup Succesfuly"
                return render(request,'login.html',{'msg':msg})
            else:
                msg = "Password & confirm password does not match"
                return render(request,'signup.html',{'msg':msg})
    else: 
        return render(request, 'signup.html')  

def login(request):
    if request.method=="POST":

        try:
            user = User.objects.get(email=request.POST['email'])

            if user.password == request.POST['password']:
                request.session['email']=user.email
                request.session['profile']=user.profile.url
                
            
                if user.usertype=="buyer":
                    return redirect('index')
                else:
                    return redirect('sindex')
            else:
                msg = "Invalid Password!!"
                return render(request,'login.html',{'msg':msg})
            
        except Exception as e:
            msg = "Invalid Email!!"
            return render(request,'login.html',{'e':e})
    else:
        

            return render(request,'login.html')


def logout(request):
    # del request.session['email']
    # del request.session['profile']
    request.session.flush()  # Clears all session data
    return redirect('login')



def fpass(request):
    if request.method == "POST":
        try:
            user = User.objects.get(mobile=request.POST['mobile'])
            mobile =  request.POST['mobile']
            otp = random.randint(1001,9999) 
            url = "https://www.fast2sms.com/dev/bulkV2"

            querystring = {"authorization":"4FLqt2yEconSrjiDwMvY19AXNB308IKZpWTkehHuxf7bVdG5aOjkV09BWEUrcpAST5JOZQs2dFoYxe8D","variables_values":str(otp),"route":"otp","numbers":str(mobile)}

            headers = {
                'cache-control': "no-cache"
            }

            response = requests.request("GET", url, headers=headers, params=querystring)

            print(response.text)
           
            request.session['mobile']=user.mobile
            request.session['otp']=otp
            
            return render(request,'otp.html')
        
        except Exception as e:
                msg = "Mobile not found!!"
                print('***************',e) 
                return render(request,'fpass.html',{'msg':msg})
    
           
    else:
        return render(request,'fpass.html')

def otp(request):
    if request.method == "POST":
        
        try:

            uotp=int(request.POST['uotp'])
            otp= int(request.session['otp'])

            uotp=int(request.POST['uotp'])
            otp= int(request.session['otp'])


            uotp = request.POST.get('uotp') 
            otp = str(request.session.get('otp')) 
            
            print(f"Session OTP: {otp}")
            print(f"User entered OTP: {uotp}")




            

            if otp == uotp:
                del request.session['otp']
                return render(request,'newpass.html')
            else:
                msg = "Invalid OTP!!"
                return render(request,'otp.html',{'msg':msg})
            
            
        except Exception as e:
            print(f"Error during OTP validation: {e}")
            return render(request,'otp.html')
            
def newpass(request):
    if request.method == "POST":
        try:
            user = User.objects.get(mobile=request.session['mobile'])
            if request.POST['npassword']==request.POST['cnpassword']:
                user.password = request.POST['npassword']
                user.save()
                del request.session['mobile']
                return redirect('login')
            else:
                msg = "New password & confirm new passwoerd does not match!!"   
                return render(request,'newpass.html',{'msg':msg})
        except User.DoesNotExist:
            msg = "User does not exist or session expired."
            return render(request, 'newpass.html', {'msg': msg})
        
        except Exception as e:
            print('***************',e)
            msg = "An unexpected error occurred. Please try again."
            return render(request, 'newpass.html', {'msg': msg})
    else:
        return render(request, 'newpass.html')
    
    
def cprofile(request):
    user = User.objects.get(email=request.session['email'])
    
    if request.method == "POST":
    
        user.name=request.POST['name']
        user.mobile=request.POST['mobile']
        try:
            user.profile = request.FILES['profile']
            user.save()
            request.session['profile']=user.profile.url
            if user.usertype=="buyer":
                return redirect('index')
            else:
                return redirect('sindex')
        except Exception as e:
            print("*******************",e)
        user.save()
        return redirect('index')
        
        
    else:
        if user.usertype=="buyer":
            return render(request,'cprofile.html',{'user':user})
        else:
            return render(request,'scprofile.html',{'user':user})
    
    
    
    
def sindex(request):
    return render(request, 'sindex.html')

def scpass(request):
    return render(request,"scpass.html")

def scprofile(request):
    return render(request,'scprofile.html')

def add(request):
    if request.method == "POST":
        seller = User.objects.get(email=request.session['email'])
        
        try:
           Product.objects.create(
               
            seller = seller,
            pname = request.POST['pname'],
            scategory = request.POST['scategory'],
            sbrand = request.POST['sbrand'],
            ssize = request.POST['ssize'],
            price = request.POST['price'],
            description = request.POST['description'],
            image = request.FILES['image']
           )
           msg = "Product added succesfully!!"
           return render(request,'add.html',{'msg':msg})
        except Exception as e:
            print("****************",e)
            return redirect('add',{'e':e})
    else:
        return render(request,'add.html')
            
            
def view(request):
    seller = User.objects.get(email = request.session['email'])
    product = Product.objects.filter(seller=seller)
    return render(request,'view.html',{'product':product})    

def update(request, pk):
    seller = User.objects.get(email=request.session['email'])
    product = Product.objects.get(pk=pk)

    if request.method == 'POST':
        product.name = request.POST.get('pname')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')

        image = request.FILES.get('image')
        if image:
            product.image = image 
          
        product.save() 

        return redirect('update', pk=product.pk) 
    else:
        return render(request, 'update.html', {'product': product})
    
def delete(request,pk):
    seller = User.objects.get(email=request.session['email'])
    product = Product.objects.get(pk=pk)
    
    product.delete()
    return redirect('view')

def shop(request):

    products = Product.objects.all()  
    return render(request, 'shop.html', {'products': products})  

def details(request,pk):
    product = Product.objects.get(pk=pk)
    return render(request, 'product-single.html', {'product': product})

def addwish(request,pk):
    user = User.objects.get(email=request.session['email'])
    product = Product.objects.get(pk=pk)
    
    Wishlist.objects.create(
        user = user,
        product = product
        
    )
    return redirect ('wishlist')

def wishlist(request):
    user = User.objects.get(email=request.session['email'])

    
    wishlist = Wishlist.objects.filter(user=user)
    
    return render(request,'wishlist.html',{'wishlist':wishlist})

def dwishlist(request,pk):
    user = User.objects.get(email=request.session['email'])
    
    wishlist = Wishlist.objects.get(pk=pk)
    
    wishlist.delete()
    
    return redirect('wishlist')

def add_to_cart(request,pk):
    user = User.objects.get(email=request.session['email'])
    product = Product.objects.get(pk=pk)
    
    cart = Cart.objects.create(
        
        user=user,
        product=product,
        price=product.price,
        qty= 1,
        # total = product.price

    )
    return redirect('shop')

def cart(request):
    try:
        user = User.objects.get(email=request.session['email'])  # Get the user based on the session
        cart_items = Cart.objects.filter(user=user,payment=False)  # Get all cart items for this user

        # Calculate total price
        total_price = 0
        for i in cart_items:
            total_price += i.product.price * i.qty
        
        payment=None
        
        if total_price > 0:
        # Razorpay payment processing
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            payment = client.order.create({'amount': total_price * 100, 'currency': 'INR', 'payment_capture': 1})

        # Create the context dictionary
        context = {
            'cart': cart_items,
            'total_price': total_price,
            'payment': payment  # Ensure payment is passed to the template
        }

    except User.DoesNotExist:
        cart_items = []
        total_price = 0
        context = {
            'cart': cart_items,
            'total_price': 0,
            'payment':None
        }

    # Pass context to template
    return render(request, 'cart.html', context)


def del_cart(request,pk):
    user = User.objects.get(email=request.session['email'])
    cart = Cart.objects.get(pk=pk)
    cart.delete()
    return redirect('cart')


def sucess(request):
    try:
        user = User.objects.get(email=request.session['email'])
        cart_items = Cart.objects.filter(user=user,payment=False)
        for i in cart_items:
            print("******************")
            i.payment=True
            i.save()
            
        return render(request,'secess.html',{'cart_items':cart_items})
    except Exception as e:
        print(e)
    return render(request,'sucess.html')