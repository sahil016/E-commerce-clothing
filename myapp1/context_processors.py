# myapp1/context_processors.py

from .models import User, Cart  # Import necessary models

def cart_count(request):
    count = 0
    try:
        # Get the user from the session using email
        user = User.objects.get(email=request.session.get('email'))
        # Count the items in the user's cart
        count = Cart.objects.filter(user=user,payment=False).count()
    except User.DoesNotExist:
        pass  # If the user doesn't exist, just leave count as 0

    return {'cart_count': count}  # Return the dictionary with the cart count
