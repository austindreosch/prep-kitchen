from flask import Flask, render_template, session, request, redirect, flash
import requests
from models import connect_db, db, User, Plan, Order
from forms import LoginForm, RegisterForm, CheckoutForm
from sqlalchemy.exc import IntegrityError
import math
# from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///prepkitchen'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = ("very_secret")

connect_db(app)
# db.create_all()

# https://postimg.cc/gallery/yZCM7f4  postimg link


CURR_USER_KEY = "current_user"


@app.route("/")
def index():
    """Home page."""

    return render_template("index.html")


@app.route('/plans')
def show_plans():
    """Show plans page. Leads to ordering page."""
    plans = Plan.query.all()

    return render_template('plans.html', plans=plans)


@app.route('/plans/<int:plan_id>')
def choose_plan(plan_id):
    """Sets chosen plan in session. Then redirects to choose menu."""
    session['cart_plan_id'] = plan_id

    plan = Plan.query.filter_by(id=plan_id).first()
    session['meal _cap'] = plan.meal_count

    session_cart = []
    id_cart = []
    cart_length = 0

    if 'cart_array' in session:
        # turn session string into a list of ids
        session_cart = session['cart_array'].lstrip(
            '["').rstrip('"]').split('","')
        id_cart = [eval(i) for i in session_cart]
        cart_length = len(id_cart)
        # reset cart if too many items for new plan
        if plan.meal_count < cart_length:
            del session['cart_array']
            session['cart_length'] = 0

    return redirect('/choose/pork')


@ app.route('/menu/<category_str>')
def query(category_str):
    """Normal menu, with api calls for menu change."""
    heading = "Menu"

    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category_str}"
    response = requests.get(url)

    data = response.json()
    meals = data['meals']
    selected_meals = []

    for meal in range(len(meals)):
        selected_meals.append(meals[meal])

    return render_template('menu.html', selected_meals=selected_meals, heading=heading, category_str=category_str)


@ app.route('/choose/<category_str>')
def menu_choose(category_str):
    """Choose menu, with buttons and shopping_cart."""

    heading = "Choose your meals."
    session_cart = []
    id_cart = []
    response_cart = []
    session['cart_length'] = 0

    # SHOPPING CART API CALLS
    if 'cart_array' in session:
        # turn session string into a list of ids
        session_cart = session['cart_array'].lstrip(
            '["').rstrip('"]').split('","')
        id_cart = [eval(i) for i in session_cart]

        cart_length = len(id_cart)
        session['cart_length'] = cart_length

    for item_id in id_cart:
        item_url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={item_id}"

        item_response = requests.get(item_url)
        item_data = item_response.json()
        item = item_data['meals']
        response_cart.append(
            {
                "idMeal": eval(item[0]["idMeal"]),
                "strMeal": item[0]["strMeal"].title(),
                "strMealThumb": item[0]["strMealThumb"]
            }
        )

    print(response_cart)

    # MENU API CALLS
    menu_url = f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category_str}"
    response = requests.get(menu_url)

    data = response.json()
    meals_json = data['meals']
    selected_meals = []

    for meal in range(len(meals_json)):
        selected_meals.append(meals_json[meal])

    # SESSION DATA
    session_plan_id = 1
    # set default plan
    if 'cart_plan_id' in session:
        session_plan_id = session['cart_plan_id']

    session_meal_cap = 3
    # set default cap
    if 'meal _cap' in session:
        session_meal_cap = session['meal _cap']

    # DATABASE PULLS
    plan = Plan.query.filter_by(id=session['cart_plan_id']).first()

    return render_template('menu-choose.html', selected_meals=selected_meals, heading=heading, session_cart=session_cart, response_cart=response_cart, session_plan_id=session_plan_id, session_meal_cap=session_meal_cap, plan=plan)


@ app.route("/cart", methods=["POST"])
def shopping_cart():
    """API for shopping_cart saving. Data sent from JS."""
    cart_array = []
    # pull the data sent from JS ajax post
    keys = request.form.keys()
    for key in keys:
        cart_array = key
    # should be able to do this without loop, as this is all data - not just cart array

    session['cart_array'] = cart_array

    return redirect(request.referrer)


@ app.route("/cart/clear")
def cart_clear():
    """POST for clearing cart session."""

    if 'cart_array' in session:
        del session['cart_array']
        session['cart_length'] = 0

    return redirect(request.referrer)


@ app.route("/checkout", methods=["GET", "POST"])
def checkout():
    """Deal with checkout, and database saving."""
    username = session['user_id']
    user = User.query.filter_by(username=username).first()
    plan = Plan.query.filter_by(id=session['cart_plan_id']).first()
    form = CheckoutForm()
    tax = math.ceil((plan.price * 0.0725) * 100) / 100
    total = math.ceil((plan.price + tax) * 100) / 100

    session_cart = []
    id_cart = []
    response_cart = []
    # SHOPPING CART API CALLS
    if 'cart_array' in session:
        # turn session string into a list of ids
        session_cart = session['cart_array'].lstrip(
            '["').rstrip('"]').split('","')
        id_cart = [eval(i) for i in session_cart]

        cart_length = len(id_cart)
        session['cart_length'] = cart_length

    for item_id in id_cart:
        item_url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={item_id}"

        item_response = requests.get(item_url)
        item_data = item_response.json()
        item = item_data['meals']
        response_cart.append(
            {
                "idMeal": eval(item[0]["idMeal"]),
                "strMeal": item[0]["strMeal"].title(),
                "strMealThumb": item[0]["strMealThumb"]
            }
        )

    if form.validate_on_submit():
        billing_name = form.billing_name.data
        billing_card = form.billing_card.data
        billing_code = form.billing_code.data
        billing_street = form.billing_street.data
        billing_city = form.billing_city.data
        billing_state = form.billing_state.data
        billing_zip = form.billing_zip.data

        meal_id1 = id_cart[0]
        meal_id2 = id_cart[1]
        meal_id3 = id_cart[2]
        if len(id_cart) > 3:
            meal_id4 = id_cart[3]
            order = Order(user_id=user.id,
                          plan_id=plan.id,
                          billing_name=billing_name,
                          billing_card=billing_card,
                          billing_code=billing_code,
                          billing_street=billing_street, billing_city=billing_city, billing_state=billing_state, billing_zip=billing_zip, price=plan.price, tax=tax, total=total, meal_id1=meal_id1, meal_id2=meal_id2, meal_id3=meal_id3, meal_id4=meal_id4)
            db.session.add(order)
            db.session.commit()
        if len(id_cart) > 4:
            meal_id5 = id_cart[4]
            order = Order(user_id=user.id, plan_id=plan.id,
                          billing_name=billing_name,
                          billing_card=billing_card,
                          billing_code=billing_code,
                          billing_street=billing_street, billing_city=billing_city, billing_state=billing_state, billing_zip=billing_zip, price=plan.price, tax=tax, total=total, meal_id1=meal_id1, meal_id2=meal_id2, meal_id3=meal_id3, meal_id4=meal_id4, meal_id5=meal_id5)
            db.session.add(order)
            db.session.commit()

        return redirect("/profile")

    return render_template('checkout.html', plan=plan, tax=tax, total=total, form=form, session_cart=session_cart, response_cart=response_cart)


@ app.route("/recipe/<int:meal_id>")
def profile_show_meal(meal_id):
    """Show recipe and ingredients for a given meal."""
    return render_template('recipe.html')


# ####################
# USERS
# ####################

@ app.route("/profile")
def profile():
    """Shows account information for a given user. Along with past orders, and links to recipes/ingredients."""
    # session['user_id'] = "adreosch1"
    # look up user id based on username
    # look up orders based on user id
    username = session['user_id']
    user = User.query.filter_by(username=username).first()

    # need "user_orders" to be the database pull for the users orders
    # need "order_meal_ids" to be the list of meal ids for each order

    user_orders = Order.query.filter_by(user_id=user.id).all()

    id_cart = [53036, 52895, 53041, 53021]
    all_orders = []

    for item_id in id_cart:
        order_list = []
        item_url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={item_id}"

        item_response = requests.get(item_url)
        item_data = item_response.json()
        item = item_data['meals']
        order_list.append(
            {
                "idMeal": eval(item[0]["idMeal"]),
                "strMeal": item[0]["strMeal"].title(),
                "strMealThumb": item[0]["strMealThumb"]
            }
        )
        all_orders.append(order_list)

    return render_template('profile.html', user=user, user_orders=user_orders, all_orders=all_orders)


@ app.route("/profile/orders")
def profile_orders():
    """Extended page for all orders. Perhaps unnecessary."""
    return render_template('orders.html')


@ app.route("/profile/edit")
def profile_edit():
    return render_template('edit.html')


@ app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome back, {user.username}!", "success")
            session['user_id'] = user.username
            return redirect('/profile')
        else:
            form.username.errors = ['Invalid username or password.']

    return render_template('login.html', form=form)


@ app.route('/logout')
def logout_user():
    session.pop('user_id')
    return redirect('/')


@ app.route('/register', methods=["GET", "POST"])
def signup():
    """Handle user signup.
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        address_street = form.address_street.data
        address_city = form.address_city.data
        address_state = form.address_state.data
        address_zip = form.address_zip.data
        subscribed = form.subscribed.data

        new_user = User.register(
            username, password, first_name, last_name, email, address_street, address_city, address_state, address_zip, subscribed)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken. Please pick another.')
            return render_template("register.html", form=form)
        flash("Your account is registered. Log in now!", "success")
        return redirect('/login')

    return render_template('register.html', form=form)
