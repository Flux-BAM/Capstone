from flask import Blueprint, render_template, request, redirect, session, jsonify, flash, current_app
import os
from models.product import Product
from models.ingredient import Ingredient
from helpers import is_logged_in, allowed_file

products_bp = Blueprint('products', __name__)

MAX_IMAGE_SIZE = 5 * 1024 * 1024


@products_bp.route('/products')
def products():
    if not is_logged_in():
        return redirect('/')
    # OOP: Product.get_all() returns a list of Product objects
    all_products = Product.get_all()
    return render_template('products.html', products=all_products, username=session['username'])


@products_bp.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if not is_logged_in():
        return redirect('/')

    # OOP: Ingredient.get_all_for_select() returns dropdown data
    ingredients = Ingredient.get_all_for_select()

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        price    = request.form.get('price', '0')
        category = request.form.get('category', '').strip()

        if not name:
            flash("Product name is required.", "danger")
            return render_template('add_product.html', ingredients=ingredients)
        if not category:
            flash("Please select a category.", "danger")
            return render_template('add_product.html', ingredients=ingredients)

        try:
            price = float(price)
        except ValueError:
            flash("Invalid price value.", "danger")
            return render_template('add_product.html', ingredients=ingredients)

        try:
            # OOP: Product.create() inserts and returns the new ID
            product_id = Product.create(name, price, category)
        except Exception:
            flash("Failed to save product.", "danger")
            return render_template('add_product.html', ingredients=ingredients)

        # handle image upload
        _save_product_image(request, product_id)

        # OOP: get the product object then save its recipe
        product = Product.get_by_id(product_id)
        ingredient_ids  = request.form.getlist('ingredient_id[]')
        ingredient_qtys = request.form.getlist('ingredient_qty[]')
        errors = product.save_recipe(ingredient_ids, ingredient_qtys)

        if errors:
            flash("Product saved, but some recipe rows had errors: " + "; ".join(errors), "warning")
        else:
            flash(f"Product '{name}' created successfully!", "success")

        return redirect('/products')

    return render_template('add_product.html', ingredients=ingredients)


@products_bp.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # OOP: get Product object first
    product = Product.get_by_id(product_id)
    if not product:
        return jsonify({"status": "error", "message": "Product not found."}), 404

    try:
        # OOP: call delete() on the object
        product.delete()

        for ext in ['jpg', 'jpeg', 'png', 'webp']:
            p = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{product_id}.{ext}")
            if os.path.exists(p):
                os.remove(p)

        return jsonify({"status": "success", "message": f"'{product.name}' deleted."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@products_bp.route('/get-recipe/<int:product_id>')
def get_recipe(product_id):
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # OOP: get Product object then call get_recipe()
    product = Product.get_by_id(product_id)
    if not product:
        return jsonify({"status": "error", "message": "Product not found"}), 404

    ingredients = product.get_recipe()
    return jsonify({
        "product":     product.name,
        "ingredients": [{"name": r["name"], "quantity": r["quantity"], "unit": r["unit"]} for r in ingredients]
    })


@products_bp.route('/edit-product/<int:product_id>', methods=['GET'])
def edit_product(product_id):
    if not is_logged_in():
        return redirect('/')

    # OOP: fetch Product object
    product = Product.get_by_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect('/products')

    ingredients = Ingredient.get_all_for_select()
    recipe      = product.get_recipe()

    return render_template('edit_product.html', product=product, ingredients=ingredients, recipe=recipe)


@products_bp.route('/edit-product/<int:product_id>', methods=['POST'])
def edit_product_save(product_id):
    if not is_logged_in():
        return redirect('/')

    # OOP: fetch Product object
    product = Product.get_by_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect('/products')

    name     = request.form.get('name', '').strip()
    price    = request.form.get('price', '0').strip()
    category = request.form.get('category', '').strip()

    if not name:
        flash("Product name is required.", "danger")
        return redirect(f'/edit-product/{product_id}')
    if not category:
        flash("Please select a category.", "danger")
        return redirect(f'/edit-product/{product_id}')

    try:
        price = float(price)
    except ValueError:
        flash("Invalid price.", "danger")
        return redirect(f'/edit-product/{product_id}')

    try:
        # OOP: update the object's attributes then call update()
        product.name     = name
        product.price    = price
        product.category = category
        product.update()
    except Exception:
        flash("Failed to update product.", "danger")
        return redirect(f'/edit-product/{product_id}')

    # handle image upload
    _save_product_image(request, product_id, replace=True)

    # OOP: save the updated recipe via the product object
    ingredient_ids  = request.form.getlist('ingredient_id[]')
    ingredient_qtys = request.form.getlist('ingredient_qty[]')
    errors = product.save_recipe(ingredient_ids, ingredient_qtys)

    if errors:
        flash("Product updated, but some recipe rows had errors: " + "; ".join(errors), "warning")
    else:
        flash(f"'{name}' updated successfully!", "success")

    return redirect('/products')


# ── PRIVATE HELPER ─────────────────────────────────────────────────────────────

def _save_product_image(req, product_id, replace=False):
    """Handle image upload for a product. Not a route — internal helper only."""
    image_file = req.files.get('image')
    if not image_file or not image_file.filename:
        return
    if not allowed_file(image_file.filename):
        flash("Invalid image format. Use JPG, PNG, or WEBP.", "warning")
        return
    image_file.seek(0, 2)
    size = image_file.tell()
    image_file.seek(0)
    if size > MAX_IMAGE_SIZE:
        flash("Image too large (max 5 MB).", "warning")
        return

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    ext = image_file.filename.rsplit('.', 1)[1].lower()

    if replace:
        for old_ext in ['jpg', 'jpeg', 'png', 'webp']:
            op = os.path.join(upload_folder, f"{product_id}.{old_ext}")
            if os.path.exists(op):
                os.remove(op)

    save_path = os.path.join(upload_folder, f"{product_id}.{ext}")
    image_file.save(save_path)

    if ext != 'jpg':
        try:
            from PIL import Image as PILImage
            img = PILImage.open(save_path).convert("RGB")
            img.save(os.path.join(upload_folder, f"{product_id}.jpg"), "JPEG", quality=90)
            os.remove(save_path)
        except ImportError:
            pass