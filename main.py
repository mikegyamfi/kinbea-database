from flask import Flask, render_template, url_for, redirect, request, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, PasswordField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo
from forms import *
from datetime import date
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user, login_user, logout_user, LoginManager, login_required

import os
import re

authorization_key = os.getenv("Auth_key")

uri = os.getenv("DATABASE_URL", "sqlite:///kinbea-shop.db")  # or other relevant config var
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = 'Michaelson'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.config["SQLALCHEMY_DATABASE_URI"] = uri
db = SQLAlchemy(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    total_quantity = db.Column(db.Integer, nullable=False)
    purchase_price = db.Column(db.Float(precision=2, decimal_return_scale=2), nullable=False)
    selling_price = db.Column(db.Float(precision=2, decimal_return_scale=2), nullable=False)
    date = db.Column(db.String(100), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    quantity_left = db.Column(db.Integer, nullable=False)
    amount_sold = db.Column(db.Float(precision=2, decimal_return_scale=2), nullable=False)
    total_amount = db.Column(db.Float(precision=2, decimal_return_scale=2), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    group_name = db.Column(db.String(100), nullable=False)


class SoldItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float(precision=2, decimal_return_scale=2), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float(precision=2, decimal_return_scale=2), nullable=False)
    status = db.Column(db.String(30), nullable=False)


class Received(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float(precision=2, decimal_return_scale=2), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float(precision=2, decimal_return_scale=2), nullable=False)
    status = db.Column(db.String(40), nullable=False)


db.create_all()


groups = ["All"]
groups_in_db = Product.query.all()
for prod in groups_in_db:
    if prod.group_name in groups:
        continue
    else:
        groups.append(prod.group_name)
clean_groups = sorted(groups, key=str.lower)


class GroupProducts(FlaskForm):
    group = SelectField("Groups", choices=groups)
    submit = SubmitField("Search")


@app.route("/", methods=['GET', 'POST'])
@login_required
def home():
    all_products = Product.query.order_by(Product.name).all()
    form = Categorize()
    group_form = GroupProducts()
    if group_form.validate_on_submit():
        if group_form.validate_on_submit():
            if group_form.group.data == "All":
                all_products = Product.query.order_by(Product.name).all()
            else:
                all_products = Product.query.filter_by(group_name=group_form.group.data).order_by(Product.name)

    if form.validate_on_submit():
        if form.category.data == "All":
            all_products = Product.query.order_by(Product.name).all()
        else:
            all_products = Product.query.filter_by(category=form.category.data).order_by(Product.name)
    today = date.today().strftime("%B %d, %Y")
    total_cost = 0
    for product in all_products:
        total_cost += product.selling_price * product.total_quantity
    formatted_total = numbers = "{:,}".format(round(total_cost, 2))
    return render_template("index.html", products=all_products, total=formatted_total, date=today, form=form, group_form=group_form)


@app.route("/add-product", methods=['GET', 'POST'])
@login_required
def add_product():
    form = AddProduct()
    if form.validate_on_submit():
        new_product = Product(
            name=form.product_name.data,
            selling_price=form.selling_price.data,
            purchase_price=form.purchase_price.data,
            total_quantity=form.product_quantity.data,
            date=date.today().strftime("%b %d, %Y"),
            quantity_sold=0,
            amount_sold=0,
            group_name=form.group_name.data,
            total_amount=form.selling_price.data * form.product_quantity.data,
            quantity_left=form.product_quantity.data,
            category=form.category.data
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('add_product'))
    return render_template("add_product.html", form=form)


@app.route("/update/<product_id>", methods=['GET', 'POST'])
@login_required
def update(product_id):
    form = Update()
    if form.validate_on_submit():
        product = Product.query.get(product_id)
        sold_item = SoldItem(
            name=product.name,
            price=product.selling_price,
            quantity_sold=form.quantity_sold.data,
            date=date.today().strftime("%b %d, %Y"),
            amount=form.quantity_sold.data * product.selling_price,
            status="Not received"
        )
        db.session.add(sold_item)
        db.session.commit()
        if product.quantity_sold + form.quantity_sold.data > product.total_quantity:
            product.quantity_sold = product.total_quantity
        else:
            product.quantity_sold += form.quantity_sold.data
        product.quantity_left = product.total_quantity - product.quantity_sold
        product.amount_sold = product.quantity_sold * product.selling_price
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("update_product.html", form=form)


@app.route("/sold")
@login_required
def sold():
    sold_products = SoldItem.query.order_by(SoldItem.id.desc()).all()
    total = 0
    for product in sold_products:
        total += product.price * product.quantity_sold
    return render_template("sold.html", products=sold_products, total=total)


@app.route("/update_status/<product_id>")
@login_required
def update_status(product_id):
    product = SoldItem.query.get(product_id)
    product.status = "Received"
    db.session.commit()
    return redirect(url_for("sold"))


@app.route("/restock/<product_id>", methods=['GET', 'POST'])
@login_required
def restock(product_id):
    item = Product.query.get(product_id)
    form = Restock(
        quantity_brought=item.quantity_left,
        purchase_price=item.purchase_price,
        selling_price=item.selling_price
    )
    if form.validate_on_submit():
        item.total_quantity = form.quantity_brought.data
        item.purchase_price = form.purchase_price.data
        item.quantity_left = form.quantity_brought.data
        item.quantity_sold = form.quantity_brought.data - form.quantity_brought.data
        item.selling_price = form.selling_price.data
        item.total_amount = form.quantity_brought.data * form.selling_price.data
        item.amount_sold = 0
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("restock.html", form=form, product=item)


@app.route("/received")
@login_required
def received():
    items_sold = SoldItem.query.all()
    for item in items_sold:
        received_amount = Received(
            name=item.name,
            price=item.price,
            quantity_sold=item.quantity_sold,
            date=date.today().strftime("%b %d, %Y"),
            amount=item.amount,
            status="Received"
        )
        db.session.add(received_amount)
        db.session.commit()
        product = SoldItem.query.get(item.id)
        db.session.delete(product)
        db.session.commit()
    return redirect(url_for('sold'))


@app.route("/show-received")
@login_required
def show_received():
    amounts_received = Received.query.order_by(Received.id.desc()).all()
    total = 0
    for product in amounts_received:
        total += product.price * product.quantity_sold
    return render_template("received.html", total=total, products=amounts_received)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = Register()
    if form.validate_on_submit():
        if str(form.authorization_key.data) != str(authorization_key):
            flash("Invalid Key. Contact your admin to be registered")
            return redirect(url_for("register"))
        else:
            new_user = User(
                name=form.name.data.title(),
                username=form.username.data,
                role=form.role.data,
                password=generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash(f"Welcome {new_user.name}")
            return redirect(url_for('home'))
    return render_template("register.html", form=form)


@app.route("/delete/<product_id>")
@login_required
def delete(product_id):
    product = Product.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete-r/<product_id>")
@login_required
def delete_r(product_id):
    product = Received.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("show_received"))


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = Login()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash("Incorrect Password")
                return redirect(url_for('login'))
        else:
            flash("Account does not exist")
            return redirect(url_for('login'))
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/users")
@login_required
def users():
    users = User.query.all()
    return render_template("users.html", users=users)


@app.route("/delete-u/<user_id>")
@login_required
def delete_u(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("users"))


@app.route("/delete-s/<product_id>")
@login_required
def delete_s(product_id):
    product = SoldItem.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("sold"))


@app.route("/edit-price/<product_id>", methods=['GET', 'POST'])
def edit_price(product_id):
    product = Product.query.get(product_id)
    form = EditPrice(
        purchase_price=product.purchase_price,
        selling_price=product.selling_price
    )
    if form.validate_on_submit():
        product.purchase_price = form.purchase_price.data
        product.selling_price = form.selling_price.data
        product.total_amount = form.selling_price.data * product.total_quantity
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit_price.html", form=form, product=product)


@app.route("/no-price")
def no_price():
    no_price_list = []
    products = Product.query.order_by(Product.name).all()
    for product in products:
        if product.selling_price == 0.1:
            no_price_list.append(product)
        else:
            continue
    return render_template("noprice.html", list=no_price_list)


if __name__ == "__main__":
    app.run(debug=True)
