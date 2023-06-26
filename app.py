from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# MySQL Database Credentials and Details
config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'db_machineproj'
}

# When entering localhost:5000
@app.route('/')
def home():
    # Connect to database
    try:
        conn = mysql.connector.connect(**config)

        if conn.is_connected():
            cursor = conn.cursor()

            # Select items for each category
            queryMains = "SELECT item_id, item_name, price, image_url FROM tbl_items WHERE category_name = 'Mains' AND inventory_qty>0"
            cursor.execute(queryMains)
            mainsList = cursor.fetchall()

            querySides = "SELECT item_id, item_name, price, image_url FROM tbl_items WHERE category_name = 'Sides' AND inventory_qty>0"
            cursor.execute(querySides)
            sidesList = cursor.fetchall()

            queryDrinks = "SELECT item_id, item_name, price, image_url FROM tbl_items WHERE category_name = 'Drinks' AND inventory_qty>0"
            cursor.execute(queryDrinks)
            drinksList = cursor.fetchall()

            return render_template('index.html', mainsList=mainsList, sidesList=sidesList, drinksList=drinksList)

    # Catch exception
    except mysql.connector.Error as err:
        print("Error connecting to MySQL: {err}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    return 'An error occurred.'

# Upon clicking checkout button
@app.route('/checkout', methods=['POST'])
def checkout():
    # Connect to db
    # Connect to database
    try:
        conn = mysql.connector.connect(**config)

        if conn.is_connected():
            cursor = conn.cursor()

            # Get item IDs and quantities from form
            mainItemID = int(request.form['mainItem'])
            sideItemID = int(request.form['sideItem'])
            drinkItemID = int(request.form['drinkItem'])

            mainItemQty = int(request.form['mainQty'])
            sideItemQty = int(request.form['sideQty'])
            drinkItemQty = int(request.form['drinkQty'])

            # Get item names and prices from database
            queryMainItem = f"SELECT item_id, item_name, price FROM tbl_items WHERE item_id = {mainItemID}"
            cursor.execute(queryMainItem)
            mainItem = cursor.fetchone()
            mainItemName = mainItem[1]
            mainItemPrice = mainItem[2]

            querySideItem = f"SELECT item_id, item_name, price FROM tbl_items WHERE item_id = {sideItemID}"
            cursor.execute(querySideItem)
            sideItem = cursor.fetchone()
            sideItemName = sideItem[1]
            sideItemPrice = sideItem[2]

            queryDrinkItem = f"SELECT item_id, item_name, price FROM tbl_items WHERE item_id = {drinkItemID}"
            cursor.execute(queryDrinkItem)
            drinkItem = cursor.fetchone()
            drinkItemName = drinkItem[1]
            drinkItemPrice = drinkItem[2]

            # TODO: Add conditional statement + separate display for when user enters quantity above the available inventory
            
            # Compute initial total price
            initialTotalPrice = (mainItemPrice * mainItemQty) + (sideItemPrice * sideItemQty) + (drinkItemPrice * drinkItemQty)

            # Identify if combo
            queryCombo = f"SELECT * FROM tbl_combos WHERE main_item_id = {mainItemID} AND side_item_id = {sideItemID} AND drink_item_id = {drinkItemID}"
            cursor.execute(queryCombo)
            comboResult = cursor.fetchone()
            if comboResult:
                print("Combo!")
                isCombo = True
                discountPct = comboResult[5]
                discount = initialTotalPrice * discountPct
                discountedTotalPrice = initialTotalPrice - discount
            else:
                print("Not combo!")
                isCombo = False
                discountPct = 0
                discount = 0
                discountedTotalPrice = initialTotalPrice

            return render_template('checkout.html', isCombo=isCombo, discountPct=discountPct, discount=discount, initialTotalPrice=initialTotalPrice, discountedTotalPrice=discountedTotalPrice, mainItemID=mainItemID, mainItemName=mainItemName, mainItemPrice=mainItemPrice, mainItemQty=mainItemQty, sideItemID=sideItemID, sideItemName=sideItemName, sideItemPrice=sideItemPrice, sideItemQty=sideItemQty, drinkItemID=drinkItemID, drinkItemName=drinkItemName, drinkItemPrice=drinkItemPrice, drinkItemQty=drinkItemQty)

    # Catch exception
    except mysql.connector.Error as err:
        print("Error connecting to MySQL: {err}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    return 'An error occurred.'

# Upon clicking Place Order button
@app.route('/placeorder', methods=['POST'])
def placeorder():
    # Connect to database
    try:
        conn = mysql.connector.connect(**config)

        if conn.is_connected():
            cursor = conn.cursor()

            # Get item IDs and quantities from form
            customerName = request.form['customerName']
            mainItemID = int(request.form['mainItemID'])
            mainItemQty = int(request.form['mainItemQty'])
            sideItemID = int(request.form['sideItemID'])
            sideItemQty = int(request.form['sideItemQty'])
            drinkItemID = int(request.form['drinkItemID'])
            drinkItemQty = int(request.form['drinkItemQty'])
            initialTotalPrice = float(request.form['initialTotalPrice'])
            discount = float(request.form['discount'])
            discountedTotalPrice = float(request.form['discountedTotalPrice'])

            # Insert into table of orders
            queryInsert = "INSERT INTO tbl_orders (customer_name, main_id, main_qty, side_id, side_qty, drink_id, drink_qty, initial_total_price, discount, discounted_total_price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            valuesInsert = (customerName, mainItemID, mainItemQty, sideItemID, sideItemQty, drinkItemID, drinkItemQty, initialTotalPrice, discount, discountedTotalPrice)
            cursor.execute(queryInsert, valuesInsert)
            conn.commit()

            # Get the newly-generated order ID
            orderID = cursor.lastrowid

            # Update inventory quantity
            queryUpdateMain = f"UPDATE tbl_items SET inventory_qty = inventory_qty - {mainItemQty} WHERE item_id = {mainItemID}"
            cursor.execute(queryUpdateMain)
            conn.commit()

            queryUpdateSide = f"UPDATE tbl_items SET inventory_qty = inventory_qty - {sideItemQty} WHERE item_id = {sideItemID}"
            cursor.execute(queryUpdateSide)
            conn.commit()

            queryUpdateDrink = f"UPDATE tbl_items SET inventory_qty = inventory_qty - {drinkItemQty} WHERE item_id = {drinkItemID}"
            cursor.execute(queryUpdateDrink)
            conn.commit()

            # Compute for the change
            amountPaid = float(request.form['amountPaid'])
            change = amountPaid - discountedTotalPrice

            return render_template('ordersuccess.html', orderID=orderID, discountedTotalPrice=discountedTotalPrice, amountPaid=amountPaid, change=change)
            

    # Catch exception
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    return 'An error occurred.'

if __name__ == '__main__':
    app.run()