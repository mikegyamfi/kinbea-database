from flask import Flask, render_template, url_for, redirect, request, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

from forms import *
from datetime import date
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user, login_user, logout_user, LoginManager, login_required

import os
import re

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
    price = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(100), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    quantity_left = db.Column(db.Integer, nullable=False)
    amount_sold = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Integer, nullable=False)


class SoldItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(40), nullable=False)


class Received(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(40), nullable=False)


db.create_all()


@app.route("/")
@login_required
def home():
    today = date.today().strftime("%B %d, %Y")
    all_products = Product.query.order_by(Product.id.desc()).all()
    total_cost = 0
    for product in all_products:
        total_cost += product.price * product.total_quantity
    return render_template("index.html", products=all_products, total=total_cost, date=today)


@app.route("/add-product", methods=['GET', 'POST'])
@login_required
def add_product():
    form = AddProduct()
    if form.validate_on_submit():
        new_product = Product(
            name=form.product_name.data,
            price=form.product_price.data,
            total_quantity=form.product_quantity.data,
            date=date.today().strftime("%b %d, %Y"),
            quantity_sold=0,
            amount_sold=0,
            total_amount=form.product_price.data * form.product_quantity.data,
            quantity_left=form.product_quantity.data
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
            price=product.price,
            quantity_sold=form.quantity_sold.data,
            date=date.today().strftime("%b %d, %Y"),
            amount=form.quantity_sold.data * product.price,
            status="Not received"
        )
        db.session.add(sold_item)
        db.session.commit()
        if product.quantity_sold + form.quantity_sold.data > product.total_quantity:
            product.quantity_sold = product.total_quantity
        else:
            product.quantity_sold += form.quantity_sold.data
        product.quantity_left = product.total_quantity - product.quantity_sold
        product.amount_sold = product.quantity_sold * product.price
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
    form = Restock()
    item = Product.query.get(product_id)
    if form.validate_on_submit():
        item.total_quantity = form.quantity_brought.data
        item.quantity_left = form.quantity_brought.data
        item.quantity_sold = form.quantity_brought.data - form.quantity_brought.data
        item.price = form.price.data
        item.total_amount = form.quantity_brought.data * form.price.data
        item.amount_sold = 0
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("restock.html", form=form)


@app.route("/received")
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
def delete(product_id):
    product = Product.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete-r/<product_id>")
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
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
