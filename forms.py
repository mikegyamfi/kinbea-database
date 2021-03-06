from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, PasswordField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo


class AddProduct(FlaskForm):
    product_name = StringField("Product Name", validators=[DataRequired()])
    product_quantity = IntegerField("Product Quantity", validators=[DataRequired()])
    purchase_price = FloatField("Purchase Price", validators=[DataRequired()])
    selling_price = FloatField("Selling Price", validators=[DataRequired()])
    group_name = StringField("Group Name", validators=[DataRequired()])
    category = SelectField("Category", choices=["Perfumes", "Oils", "ToothPastes", "Tubes", "Soaps", "Creams", "Lotions", "Wigs", "Toilet Papers", "Underwear", "Relaxers", "Makeups", "Roll-on", "Glycerine", "Styling Gel", "Shower Gel", "Cleanser", "Hair Dye", "Hand Sanitizer", "Shampoo", "Conditioner", "Powder", "Setting Lotion", "Spiritz", "Spray", "Deodorant Spray","Detergent", "ToothBrush", "Pampers", "Others"])
    submit = SubmitField("Add Product")


class Update(FlaskForm):
    quantity_sold = IntegerField("Quantity Sold")
    submit = SubmitField('Update')


class Restock(FlaskForm):
    quantity_brought = IntegerField("Quantity")
    purchase_price = FloatField("Purchase Price")
    selling_price = FloatField("Selling Price")
    submit = SubmitField('Restock')


class Register(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    role = SelectField("Role", choices=[("Admin"), ("Sales Personel")], default=("Sales Personel"),  validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), EqualTo("confirm_password", "Passwords don't match")])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    authorization_key = IntegerField("Authorization Key")
    submit = SubmitField('Register')


class Login(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField('Login')


class Categorize(FlaskForm):
    category = SelectField("Category", choices=["All", "Perfumes", "Oils", "ToothPastes", "Tubes", "Soaps", "Creams", "Lotions", "Wigs", "Toilet Papers", "Underwear", "Relaxers", "Makeups", "Roll-on", "Glycerine", "Styling Gel", "Shower Gel", "Cleanser", "Hair Dye", "Hand Sanitizer", "Shampoo", "Conditioner", "Powder", "Setting Lotion", "Spiritz", "Spray", "Deodorant Spray", "Detergent", "ToothBrush", "Pampers", "Others"])
    submit = SubmitField("Search")


class EditPrice(FlaskForm):
    purchase_price = FloatField("Purchase Price")
    selling_price = FloatField("Selling Price")
    submit = SubmitField("Edit Price")
