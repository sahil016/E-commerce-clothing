# E-Commerce Clothing Store

A full-stack clothing store built with **Django**. Sellers list and manage products, buyers browse, save items to a wishlist, add them to a cart and pay online with **Razorpay**.

## Features

**Accounts**
- Sign up as a **buyer** or a **seller**, with an optional profile photo
- Login and logout with hashed passwords
- Change password and edit profile
- Forgot password with a **one-time code sent by email** (expires after 5 minutes)

**Buyers**
- Browse the shop and view product details
- Wishlist: add and remove items
- Cart: quantity updates and remove items
- Online payment through Razorpay, with server-side signature verification

**Sellers**
- Add products with image, category, brand, size, price and description
- View, edit and delete their own products only

**Security**
- Passwords stored as hashes
- Pages require login, and sellers and buyers see only their own data
- Razorpay payments are verified before an order is marked paid
- Secrets are kept in a `.env` file, not in the code

## Tech Stack

- Python, Django
- SQLite
- Razorpay (payments)
- Gmail SMTP (OTP emails)
- HTML, CSS, JavaScript

## Screenshots

<!-- Add screenshots here, for example:
![Home page](screenshots/home.png)
![Cart](screenshots/cart.png)
-->

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/sahil016/E-commerce-clothing.git
   cd E-commerce-clothing
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS / Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create your `.env` file**

   Copy `.env.example` to `.env` and fill in your own values (see below).

5. **Set up the database**
   ```bash
   python manage.py migrate
   ```

6. **Run the server**
   ```bash
   python manage.py runserver
   ```
   Open http://127.0.0.1:8000/

## Environment variables

| Variable | Description |
|---|---|
| `RAZORPAY_KEY_ID` | Razorpay key id (use **test** keys while developing) |
| `RAZORPAY_KEY_SECRET` | Razorpay key secret |
| `EMAIL_HOST_USER` | Gmail address that sends the OTP emails |
| `EMAIL_HOST_PASSWORD` | Gmail **app password** (16 characters, not your normal password) |

The names must match what your `settings.py` reads. Never commit `.env`.

### Getting a Gmail app password
1. Turn on 2-Step Verification for the sender Gmail account.
2. Open `myaccount.google.com/apppasswords` and create a password.
3. Paste it into `.env` without spaces.

During development, if `DEBUG = True` and the email fails, the OTP is printed in the terminal so you can keep testing.

## Payment flow

1. The cart page creates a Razorpay order and tags the cart items with its order id.
2. The buyer pays in the Razorpay checkout.
3. Razorpay sends the buyer to `/sucess/` with the payment id, order id and signature.
4. The server verifies the signature and the order amount, then marks the cart items as paid.

## Author

**Sahil**: [github.com/sahil016](https://github.com/sahil016)
