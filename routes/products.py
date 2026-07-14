from flask import Blueprint, render_template, request, redirect, session, jsonify, flash
import MySQLdb.cursors
import os
from extensions import mysql
from helpers import is_logged_in, allowed_file

products_bp = Blueprint('products', __name__)

MAX_IMAGE_SIZE = 5 * 1024 * 1024


@products_bp.route('/products')
def products():
    if not is_logged_in():
        return redirect('/')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM products ORDER BY name ASC")
    products = cursor.fetchall()
    return render_template('products.html', products=products, username=session['username'])


@products_bp.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, name, unit FROM ingredients ORDER BY name ASC")
    ingredients = cursor.fetchall()

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
            cursor.execute(
                "INSERT INTO products (name, price, stock, category) VALUES (%s, %s, %s, %s)",
                (name, price, 0, category)
            )
            mysql.connection.commit()
            product_id = cursor.lastrowid
        except Exception:
            mysql.connection.rollback()
            flash("Failed to save product.", "danger")
            return render_template('add_product.html', ingredients=ingredients)

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                flash("Invalid image format. Use JPG, PNG, or WEBP.", "warning")
            else:
                image_file.seek(0, 2); size = image_file.tell(); image_file.seek(0)
                if size > MAX_IMAGE_SIZE:
                    flash("Image too large (max 5 MB).", "warning")
                else:
                    from flask import current_app
                    ext       = image_file.filename.rsplit('.', 1)[1].lower()
                    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{product_id}.{ext}")
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    image_file.save(save_path)
                    if ext != 'jpg':
                        try:
                            from PIL import Image as PILImage
                            img = PILImage.open(save_path).convert("RGB")
                            img.save(os.path.join(current_app.config['UPLOAD_FOLDER'], f"{product_id}.jpg"), "JPEG", quality=90)
                            os.remove(save_path)
                        except ImportError:
                            pass

        ingredient_ids  = request.form.getlist('ingredient_id[]')
        ingredient_qtys = request.form.getlist('ingredient_qty[]')
        recipe_errors   = []

        for ing_id, qty in zip(ingredient_ids, ingredient_qtys):
            ing_id = ing_id.strip(); qty = qty.strip()
            if not ing_id or not qty: continue
            try:
                qty_val = float(qty)
                if qty_val <= 0: raise ValueError
            except ValueError:
                recipe_errors.append(f"Invalid qty for ingredient ID {ing_id}"); continue
            try:
                cursor.execute(
                    "INSERT INTO recipes (product_id, ingredient_id, quantity) VALUES (%s,%s,%s)",
                    (product_id, ing_id, qty_val)
                )
            except Exception:
                recipe_errors.append(f"Could not link ingredient ID {ing_id}")

        mysql.connection.commit()

        if recipe_errors:
            flash("Product saved, but some recipe rows had errors: " + "; ".join(recipe_errors), "warning")
        else:
            flash(f"Product '{name}' created successfully!", "success")

        return redirect('/products')

    return render_template('add_product.html', ingredients=ingredients)


@products_bp.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT name FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({"status": "error", "message": "Product not found."}), 404

    try:
        cursor.execute("DELETE FROM recipes    WHERE product_id = %s", (product_id,))
        cursor.execute("DELETE FROM sale_items WHERE product_id = %s", (product_id,))
        cursor.execute("DELETE FROM products   WHERE id = %s",         (product_id,))
        mysql.connection.commit()

        from flask import current_app
        for ext in ['jpg', 'jpeg', 'png', 'webp']:
            p = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{product_id}.{ext}")
            if os.path.exists(p): os.remove(p)

        return jsonify({"status": "success", "message": f"'{product['name']}' deleted."})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@products_bp.route('/get-recipe/<int:product_id>')
def get_recipe(product_id):
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT name FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({"status": "error", "message": "Product not found"}), 404

    cursor.execute("""
        SELECT i.name, r.quantity, i.unit
        FROM recipes r
        JOIN ingredients i ON r.ingredient_id = i.id
        WHERE r.product_id = %s
        ORDER BY i.name ASC
    """, (product_id,))
    rows = cursor.fetchall()

    ingredients = [{"name": r["name"], "quantity": r["quantity"], "unit": r["unit"]} for r in rows]

    return jsonify({"product": product["name"], "ingredients": ingredients})


@products_bp.route('/edit-product/<int:product_id>', methods=['GET'])
def edit_product(product_id):
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    if not product:
        flash("Product not found.", "danger")
        return redirect('/products')

    cursor.execute("SELECT id, name, unit FROM ingredients ORDER BY name ASC")
    ingredients = cursor.fetchall()

    cursor.execute("""
        SELECT r.ingredient_id, r.quantity, i.name AS ingredient_name, i.unit
        FROM recipes r JOIN ingredients i ON r.ingredient_id = i.id
        WHERE r.product_id = %s ORDER BY i.name ASC
    """, (product_id,))
    recipe = cursor.fetchall()

    return render_template('edit_product.html', product=product, ingredients=ingredients, recipe=recipe)


@products_bp.route('/edit-product/<int:product_id>', methods=['POST'])
def edit_product_save(product_id):
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
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
        cursor.execute("UPDATE products SET name=%s, price=%s, category=%s WHERE id=%s", (name, price, category, product_id))
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        flash("Failed to update product.", "danger")
        return redirect(f'/edit-product/{product_id}')

    image_file = request.files.get('image')
    if image_file and image_file.filename:
        if not allowed_file(image_file.filename):
            flash("Invalid image format.", "warning")
        else:
            image_file.seek(0, 2); size = image_file.tell(); image_file.seek(0)
            if size > MAX_IMAGE_SIZE:
                flash("Image too large (max 5 MB).", "warning")
            else:
                from flask import current_app
                ext       = image_file.filename.rsplit('.', 1)[1].lower()
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{product_id}.{ext}")
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                for old_ext in ['jpg', 'jpeg', 'png', 'webp']:
                    op = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{product_id}.{old_ext}")
                    if os.path.exists(op): os.remove(op)
                image_file.save(save_path)
                if ext != 'jpg':
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(save_path).convert("RGB")
                        img.save(os.path.join(current_app.config['UPLOAD_FOLDER'], f"{product_id}.jpg"), "JPEG", quality=90)
                        os.remove(save_path)
                    except ImportError:
                        pass

    ingredient_ids  = request.form.getlist('ingredient_id[]')
    ingredient_qtys = request.form.getlist('ingredient_qty[]')

    try:
        cursor.execute("DELETE FROM recipes WHERE product_id = %s", (product_id,))
        recipe_errors = []
        for ing_id, qty in zip(ingredient_ids, ingredient_qtys):
            ing_id = ing_id.strip(); qty = qty.strip()
            if not ing_id or not qty: continue
            try:
                qty_val = float(qty)
                if qty_val <= 0: raise ValueError
            except ValueError:
                recipe_errors.append(f"Invalid qty for ingredient ID {ing_id}"); continue
            cursor.execute(
                "INSERT INTO recipes (product_id, ingredient_id, quantity) VALUES (%s,%s,%s)",
                (product_id, ing_id, qty_val)
            )
        mysql.connection.commit()

        if recipe_errors:
            flash("Product updated, but some recipe rows had errors: " + "; ".join(recipe_errors), "warning")
        else:
            flash(f"'{name}' updated successfully!", "success")
    except Exception:
        mysql.connection.rollback()
        flash("Product details saved, but failed to update recipe.", "warning")

    return redirect('/products')