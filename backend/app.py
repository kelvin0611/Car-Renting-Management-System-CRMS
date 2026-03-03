import os

from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime
from flask_cors import CORS
from dotenv import load_dotenv

import bcrypt
import csv
import io

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)
CORS(app)

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "p2p_car_rental"),
    )

def _is_admin_active(user: dict) -> bool:
    return (user or {}).get("userType") == "admin" and (user or {}).get("userStatus", "active") == "active"

def _get_user_by_id(user_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `User` WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user

def _get_owner_id_for_user(user_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT owner_id FROM Owner WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row[0] if row else None

# User Registration
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT user_id FROM `User` WHERE gmail = %s", (data['gmail'],))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 400

        # Check password
        if 'password' not in data or not data['password']:
            return jsonify({'error': 'Password cannot be empty'}), 400

        password_hash = bcrypt.hashpw(
            data["password"].encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
        
        # Insert into User table
        sql = "INSERT INTO `User` (userType, name, gmail, identityNo, address, password, userStatus, createTime, updateTime) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        now = datetime.now()
        cursor.execute(sql, (data['userType'], data['name'], data['gmail'], data['identityNo'], data['address'], password_hash, 'active', now, now))
        user_id = cursor.lastrowid
        
        # Create Renter or Owner record based on user type
        if data['userType'] == 'renter':
            cursor.execute("INSERT INTO Renter (user_id, rating, balance) VALUES (%s, %s, %s)", 
                          (user_id, 5.0, 0.0))
        elif data['userType'] == 'owner':
            cursor.execute("INSERT INTO Owner (user_id, rating) VALUES (%s, %s)", 
                          (user_id, 5.0))
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'msg': 'Registration successful', 'user_id': user_id}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User Login
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        gmail = (data.get('gmail') or '').strip()
        password = (data.get('password') or '').strip()
        if not gmail or not password:
            return jsonify({'error': 'Email and password cannot be empty'}), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM `User` WHERE gmail = %s", (gmail,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if not user:
            return jsonify({'error': 'User does not exist'}), 404
        if user.get("userStatus", "active") != "active":
            return jsonify({'error': 'User is disabled'}), 403

        stored_hash = user.get("password") or ""
        try:
            ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            ok = False

        if not ok:
            return jsonify({'error': 'Incorrect password'}), 401

        return jsonify({'msg': 'Login successful', 'user_id': user['user_id'], 'userType': user['userType']}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get User Information
@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM `User` WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user:
            return jsonify(user)
        else:
            return jsonify({'error': 'User does not exist'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get User's Renter ID
@app.route('/user/<int:user_id>/renter', methods=['GET'])
def get_renter_id(user_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # First check if user exists
        cursor.execute("SELECT userType FROM `User` WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User does not exist'}), 404
        
        if user['userType'] != 'renter':
            return jsonify({'error': 'User is not a renter type'}), 400
        
        # Get renter_id
        cursor.execute("SELECT renter_id FROM Renter WHERE user_id = %s", (user_id,))
        renter = cursor.fetchone()
        cursor.close()
        db.close()
        
        if renter:
            return jsonify({'renter_id': renter['renter_id']})
        else:
            return jsonify({'error': 'Renter record not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Search Vehicles
@app.route('/vehicles', methods=['GET'])
def search_vehicles():
    try:
        carType = request.args.get('carType')
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Use case-insensitive status check
        sql = "SELECT * FROM Vehicle WHERE LOWER(status) = 'available'"
        
        filters = []
        params = []
        
        if carType:
            filters.append("carType LIKE %s")
            params.append(f"%{carType}%")
        
        if min_price:
            filters.append("dailyPrice >= %s")
            params.append(float(min_price))
        
        if max_price:
            filters.append("dailyPrice <= %s")
            params.append(float(max_price))
        
        if filters:
            sql += " AND " + " AND ".join(filters)
        
        cursor.execute(sql, params)
        vehicles = cursor.fetchall()
        
        cursor.close()
        db.close()
        return jsonify(vehicles)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Vehicle Details
@app.route('/vehicles/<int:vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Vehicle WHERE vehicle_id = %s", (vehicle_id,))
        vehicle = cursor.fetchone()
        cursor.close()
        db.close()
        
        if vehicle:
            return jsonify(vehicle)
        else:
            return jsonify({'error': 'Vehicle does not exist'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get All Insurance Options
@app.route('/insurances', methods=['GET'])
def get_insurances():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Insurance ORDER BY fee")
        insurances = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(insurances)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Specific Insurance Details
@app.route('/insurances/<int:insurance_id>', methods=['GET'])
def get_insurance(insurance_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Insurance WHERE insurance_id = %s", (insurance_id,))
        insurance = cursor.fetchone()
        cursor.close()
        db.close()
        
        if insurance:
            return jsonify(insurance)
        else:
            return jsonify({'error': 'Insurance does not exist'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Create Rental with Insurance Information
@app.route('/rent', methods=['POST'])
def rent_vehicle():
    try:
        data = request.json
        
        db = get_db()
        cursor = db.cursor()
        
        # Validate required fields
        required_fields = ['vehicle_id', 'user_id', 'rentalStartTime', 'rentalEndTime', 'pickupLocation', 'dropoffLocation']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # First get user's renter_id
        cursor.execute("SELECT renter_id FROM Renter WHERE user_id = %s", (data['user_id'],))
        renter = cursor.fetchone()
        
        if not renter:
            return jsonify({'error': 'User is not a renter or renter record not found'}), 400
        
        renter_id = renter[0]
        
        # Get vehicle information to calculate total amount
        cursor.execute("SELECT dailyPrice, status FROM Vehicle WHERE vehicle_id = %s", (data['vehicle_id'],))
        vehicle = cursor.fetchone()
        
        if not vehicle:
            return jsonify({'error': 'Vehicle does not exist'}), 404
        
        # Check vehicle status
        vehicle_status = vehicle[1].lower() if vehicle[1] else ''
        
        if vehicle_status != 'available':
            return jsonify({'error': f'Vehicle not available, current status: {vehicle[1]}'}), 400
        
        daily_price = float(vehicle[0])
        
        # Calculate rental days
        try:
            start_time = datetime.fromisoformat(data['rentalStartTime'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(data['rentalEndTime'].replace('Z', '+00:00'))
            rental_days = max(1, (end_time - start_time).days)
            base_amount = daily_price * rental_days
        except Exception as e:
            return jsonify({'error': f'Date format error: {str(e)}'}), 400
        
        # Calculate insurance fee
        insurance_fee = 0.0
        insurance_id = data.get('insurance_id')
        if insurance_id is not None:
            try:
                insurance_id_int = int(insurance_id)
            except Exception:
                insurance_id_int = None
        else:
            insurance_id_int = None

        if insurance_id_int:
            cursor.execute("SELECT fee FROM Insurance WHERE insurance_id = %s", (insurance_id_int,))
            insurance = cursor.fetchone()
            if insurance:
                insurance_fee = float(insurance[0])
        
        total_amount = base_amount + insurance_fee
        
        pickup_location = data.get("pickupLocation")
        dropoff_location = data.get("dropoffLocation")

        # Create rental order (with insurance information)
        if insurance_id_int:
            sql = """INSERT INTO Rental (vehicle_id, renter_id, insurance_id, rentalStartTime, rentalEndTime, pickupLocation, dropoffLocation, totalAmount, orderStatus, paymentStatus, dailyPrice, createTime)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (
                data['vehicle_id'], renter_id, insurance_id_int, data['rentalStartTime'], 
                data['rentalEndTime'], pickup_location, dropoff_location, total_amount, 'pending', 'unpaid', daily_price, datetime.now()
            ))
        else:
            sql = """INSERT INTO Rental (vehicle_id, renter_id, rentalStartTime, rentalEndTime, pickupLocation, dropoffLocation, totalAmount, orderStatus, paymentStatus, dailyPrice, createTime)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (
                data['vehicle_id'], renter_id, data['rentalStartTime'], 
                data['rentalEndTime'], pickup_location, dropoff_location, total_amount, 'pending', 'unpaid', daily_price, datetime.now()
            ))
        
        # Get last inserted ID
        rental_id = cursor.lastrowid
        
        # Update vehicle status to rented
        cursor.execute("UPDATE Vehicle SET status = 'rented' WHERE vehicle_id = %s", (data['vehicle_id'],))
        
        # Commit transaction
        db.commit()
        
        cursor.close()
        db.close()
        
        return jsonify({
            'msg': 'Booking successful', 
            'rental_id': rental_id, 
            'totalAmount': total_amount,
            'baseAmount': base_amount,
            'insuranceFee': insurance_fee,
            'renter_id': renter_id
        }), 201
        
    except Exception as e:
        if 'db' in locals() and db.is_connected():
            db.rollback()
            cursor.close()
            db.close()
        return jsonify({'error': str(e)}), 500

# Payment
@app.route('/pay', methods=['POST'])
def pay():
    try:
        data = request.json
        
        rental_id = data['rental_id']
        
        db = get_db()
        cursor = db.cursor()
        
        # First verify rental order exists
        cursor.execute("SELECT * FROM Rental WHERE rental_id = %s", (rental_id,))
        rental = cursor.fetchone()
        
        if not rental:
            return jsonify({'error': 'Rental order does not exist'}), 404
        
        # Create payment record
        sql = """INSERT INTO Payment (rental_id, paymentAmount, paymentMethod, paymentTime, TransactionNumber, paymentStatus)
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (
            data['rental_id'], data['paymentAmount'], data['paymentMethod'],
            datetime.now(), data['TransactionNumber'], 'paid'
        ))
        
        # Update order payment status and order status
        cursor.execute("UPDATE Rental SET paymentStatus='paid', orderStatus='confirmed' WHERE rental_id=%s", (data['rental_id'],))
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'msg': 'Payment successful', 'payment_status': 'paid'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Order Details (for success page display)
@app.route('/order/<int:rental_id>', methods=['GET'])
def get_order_details(rental_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                r.rental_id,
                r.rentalStartTime,
                r.rentalEndTime,
                r.totalAmount,
                r.orderStatus,
                r.paymentStatus,
                v.carType,
                v.brand,
                v.model,
                v.year,
                u.name as renter_name,
                p.paymentMethod,
                p.paymentTime,
                p.TransactionNumber
            FROM Rental r
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
            JOIN Renter rt ON r.renter_id = rt.renter_id
            JOIN `User` u ON rt.user_id = u.user_id
            LEFT JOIN Payment p ON r.rental_id = p.rental_id
            WHERE r.rental_id = %s
        """, (rental_id,))
        
        order = cursor.fetchone()
        cursor.close()
        db.close()
        
        if order:
            return jsonify(order)
        else:
            return jsonify({'error': 'Order does not exist'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Vehicle Details (for payment page)
@app.route('/rental/<int:rental_id>/vehicle', methods=['GET'])
def get_rental_vehicle(rental_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT v.* 
            FROM Vehicle v
            JOIN Rental r ON v.vehicle_id = r.vehicle_id
            WHERE r.rental_id = %s
        """, (rental_id,))
        
        vehicle = cursor.fetchone()
        cursor.close()
        db.close()
        
        if vehicle:
            return jsonify(vehicle)
        else:
            return jsonify({'error': 'Vehicle information does not exist'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Return Vehicle
@app.route('/return', methods=['POST'])
def return_vehicle():
    try:
        data = request.json
        
        rental_id = data['rental_id']
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Get rental order details
        cursor.execute("""
            SELECT r.*, v.vehicle_id, v.status as vehicle_status 
            FROM Rental r 
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id 
            WHERE r.rental_id = %s
        """, (rental_id,))
        rental = cursor.fetchone()
        
        if not rental:
            return jsonify({'error': 'Rental order does not exist'}), 404
        
        # Check if order is already completed
        if rental['orderStatus'] == 'completed':
            return jsonify({'error': 'Vehicle already returned'}), 400
        
        # Update order status to completed
        cursor.execute("UPDATE Rental SET orderStatus = 'completed', returnTime = %s WHERE rental_id = %s", 
                      (datetime.now(), rental_id))
        
        # Update vehicle status to available
        cursor.execute("UPDATE Vehicle SET status = 'available' WHERE vehicle_id = %s", 
                      (rental['vehicle_id'],))
        
        # Commit transaction
        db.commit()
        
        cursor.close()
        db.close()
        
        return jsonify({
            'msg': 'Vehicle return successful', 
            'order_status': 'completed',
            'vehicle_status': 'available'
        }), 200
        
    except Exception as e:
        if 'db' in locals() and db.is_connected():
            db.rollback()
            cursor.close()
            db.close()
        return jsonify({'error': str(e)}), 500

# Get User's Rental History
@app.route('/user/<int:user_id>/rentals', methods=['GET'])
def get_user_rentals(user_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Get user's rental records
        cursor.execute("""
            SELECT r.*, v.carType, v.brand, v.model, v.dailyPrice,
                   i.types as insurance_type, i.fee as insurance_fee
            FROM Rental r
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
            JOIN Renter rt ON r.renter_id = rt.renter_id
            LEFT JOIN Insurance i ON r.insurance_id = i.insurance_id
            WHERE rt.user_id = %s
            ORDER BY r.rentalStartTime DESC
        """, (user_id,))
        
        rentals = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(rentals)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Check if Rental Can Be Returned
@app.route('/rental/<int:rental_id>/can_return', methods=['GET'])
def can_return_rental(rental_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT r.*, v.carType, v.brand, v.model, 
                   CASE 
                       WHEN r.orderStatus = 'confirmed' AND r.paymentStatus = 'paid' THEN 1
                       ELSE 0
                   END as can_return
            FROM Rental r
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
            WHERE r.rental_id = %s
        """, (rental_id,))
        
        rental = cursor.fetchone()
        cursor.close()
        db.close()
        
        if rental:
            return jsonify(rental)
        else:
            return jsonify({'error': 'Rental order does not exist'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Renter: cancel rental (only unpaid pending/confirmed)
@app.route('/rental/<int:rental_id>/cancel', methods=['POST'])
def cancel_rental(rental_id):
    try:
        data = request.json or {}
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT renter_id FROM Renter WHERE user_id = %s", (int(user_id),))
        renter = cursor.fetchone()
        if not renter:
            cursor.close()
            db.close()
            return jsonify({'error': 'User is not a renter'}), 400

        renter_id = renter["renter_id"]
        cursor.execute("SELECT * FROM Rental WHERE rental_id = %s AND renter_id = %s", (rental_id, renter_id))
        rental = cursor.fetchone()
        if not rental:
            cursor.close()
            db.close()
            return jsonify({'error': 'Rental order does not exist'}), 404

        if rental.get("paymentStatus") == "paid":
            cursor.close()
            db.close()
            return jsonify({'error': 'Paid orders cannot be cancelled in current flow'}), 400

        if rental.get("orderStatus") not in ("pending", "confirmed"):
            cursor.close()
            db.close()
            return jsonify({'error': 'Only pending/confirmed orders can be cancelled'}), 400

        vehicle_id = rental.get("vehicle_id")

        cursor2 = db.cursor()
        cursor2.execute("UPDATE Rental SET orderStatus = 'cancelled' WHERE rental_id = %s", (rental_id,))
        if vehicle_id:
            cursor2.execute("UPDATE Vehicle SET status = 'available' WHERE vehicle_id = %s", (vehicle_id,))
        db.commit()
        cursor2.close()
        cursor.close()
        db.close()
        return jsonify({'msg': 'Rental cancelled'}), 200
    except Exception as e:
        if 'db' in locals() and db.is_connected():
            db.rollback()
            cursor2.close() if 'cursor2' in locals() else None
            cursor.close() if 'cursor' in locals() else None
            db.close()
        return jsonify({'error': str(e)}), 500

# Renter: extend rental end time (requires additional payment if already paid)
@app.route('/rental/<int:rental_id>/extend', methods=['POST'])
def extend_rental(rental_id):
    try:
        data = request.json or {}
        user_id = data.get("user_id")
        new_end = data.get("rentalEndTime")
        if not user_id or not new_end:
            return jsonify({'error': 'Missing user_id or rentalEndTime'}), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT renter_id FROM Renter WHERE user_id = %s", (int(user_id),))
        renter = cursor.fetchone()
        if not renter:
            cursor.close()
            db.close()
            return jsonify({'error': 'User is not a renter'}), 400
        renter_id = renter["renter_id"]

        cursor.execute("SELECT * FROM Rental WHERE rental_id = %s AND renter_id = %s", (rental_id, renter_id))
        rental = cursor.fetchone()
        if not rental:
            cursor.close()
            db.close()
            return jsonify({'error': 'Rental order does not exist'}), 404

        if rental.get("orderStatus") in ("completed", "cancelled"):
            cursor.close()
            db.close()
            return jsonify({'error': 'Order cannot be extended'}), 400

        # Parse dates
        start_time = rental["rentalStartTime"]
        try:
            new_end_time = datetime.fromisoformat(str(new_end).replace('Z', '+00:00'))
        except Exception as e:
            cursor.close()
            db.close()
            return jsonify({'error': f'Date format error: {str(e)}'}), 400

        if new_end_time <= start_time:
            cursor.close()
            db.close()
            return jsonify({'error': 'End time must be after start time'}), 400

        daily_price = float(rental.get("dailyPrice") or 0)
        rental_days = max(1, (new_end_time - start_time).days)
        base_amount = daily_price * rental_days

        insurance_fee = 0.0
        insurance_id = rental.get("insurance_id")
        if insurance_id:
            cursor.execute("SELECT fee FROM Insurance WHERE insurance_id = %s", (insurance_id,))
            row = cursor.fetchone()
            if row and row.get("fee") is not None:
                insurance_fee = float(row["fee"])

        new_total = base_amount + insurance_fee
        old_total = float(rental.get("totalAmount") or 0)

        cursor2 = db.cursor()
        cursor2.execute(
            "UPDATE Rental SET rentalEndTime = %s, totalAmount = %s, paymentStatus = %s WHERE rental_id = %s",
            (new_end_time, new_total, 'unpaid', rental_id),
        )

        # If already paid before, record extra amount due as a pending Payment row (optional)
        extra = max(0.0, new_total - old_total)
        if rental.get("paymentStatus") == "paid" and extra > 0:
            cursor2.execute(
                "INSERT INTO Payment (rental_id, paymentAmount, paymentMethod, paymentTime, TransactionNumber, paymentStatus) VALUES (%s, %s, %s, %s, %s, %s)",
                (rental_id, extra, 'adjustment', datetime.now(), f'EXTEND-{rental_id}-{int(datetime.now().timestamp())}', 'pending'),
            )

        db.commit()
        cursor2.close()
        cursor.close()
        db.close()
        return jsonify({'msg': 'Rental extended', 'newTotalAmount': new_total, 'extraDue': extra}), 200
    except Exception as e:
        if 'db' in locals() and db.is_connected():
            db.rollback()
            cursor2.close() if 'cursor2' in locals() else None
            cursor.close() if 'cursor' in locals() else None
            db.close()
        return jsonify({'error': str(e)}), 500

# Renter: list payments for a rental (receipt)
@app.route('/rental/<int:rental_id>/payments', methods=['GET'])
def get_rental_payments(rental_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Payment WHERE rental_id = %s ORDER BY paymentTime DESC, payment_id DESC", (rental_id,))
        rows = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin Login - Based on User table admin users
@app.route('/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.json
        gmail = (data.get('gmail') or '').strip()
        password = (data.get('password') or '').strip()
        
        if not gmail or not password:
            return jsonify({'error': 'Email and password cannot be empty'}), 400
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Query admin user - modified to query User table with userType as admin
        cursor.execute("SELECT * FROM `User` WHERE gmail = %s AND userType = 'admin'", (gmail,))
        admin_user = cursor.fetchone()
        
        if not admin_user:
            return jsonify({'error': 'Admin account does not exist'}), 401
        if admin_user.get("userStatus", "active") != "active":
            return jsonify({'error': 'Admin account is disabled'}), 403
        
        stored_hash = admin_user.get("password") or ""
        try:
            ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            ok = False

        if not ok:
            return jsonify({'error': 'Incorrect password'}), 401
        
        cursor.close()
        db.close()
        
        return jsonify({
            'msg': 'Admin login successful',
            'admin_id': admin_user['user_id'],  # Return user_id as admin_id
            'username': admin_user['gmail'],
            'full_name': admin_user['name'],
            'userType': admin_user['userType']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get All User Information
@app.route('/admin/users', methods=['GET'])
def get_all_users():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        userType = request.args.get("userType")
        gmail = request.args.get("gmail")
        userStatus = request.args.get("userStatus")

        where = []
        params = []
        if userType:
            where.append("u.userType = %s")
            params.append(userType)
        if gmail:
            where.append("u.gmail LIKE %s")
            params.append(f"%{gmail}%")
        if userStatus:
            where.append("u.userStatus = %s")
            params.append(userStatus)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        cursor.execute("""
            SELECT 
                u.user_id,
                u.userType,
                u.userStatus,
                u.name,
                u.gmail,
                u.identityNo,
                u.address,
                u.password,
                CASE 
                    WHEN u.userType = 'renter' THEN r.renter_id
                    WHEN u.userType = 'owner' THEN o.owner_id
                    ELSE NULL
                END as type_id,
                CASE 
                    WHEN u.userType = 'renter' THEN r.rating
                    WHEN u.userType = 'owner' THEN o.rating
                    ELSE NULL
                END as rating,
                CASE 
                    WHEN u.userType = 'renter' THEN r.balance
                    ELSE NULL
                END as balance
            FROM `User` u
            LEFT JOIN Renter r ON u.user_id = r.user_id
            LEFT JOIN Owner o ON u.user_id = o.user_id
            {where_sql}
            ORDER BY u.user_id
        """.format(where_sql=where_sql), params)
        
        users = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(users)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update User Password
@app.route('/admin/users/<int:user_id>/password', methods=['PUT'])
def update_user_password(user_id):
    try:
        data = request.json
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({'error': 'New password cannot be empty'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        password_hash = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

        cursor.execute("UPDATE `User` SET password = %s WHERE user_id = %s", 
                      (password_hash, user_id))
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'msg': 'Password updated successfully'}), 200
        
    except Exception as e:
        if 'db' in locals() and db.is_connected():
            db.rollback()
            cursor.close()
            db.close()
        return jsonify({'error': str(e)}), 500

# Delete User
@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # First get user type
        cursor.execute("SELECT userType FROM `User` WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User does not exist'}), 404
        
        user_type = user[0]
        
        # Delete related records based on user type
        if user_type == 'renter':
            # Delete rental records
            cursor.execute("DELETE FROM Rental WHERE renter_id IN (SELECT renter_id FROM Renter WHERE user_id = %s)", (user_id,))
            # Delete renter record
            cursor.execute("DELETE FROM Renter WHERE user_id = %s", (user_id,))
        elif user_type == 'owner':
            # Delete vehicle records
            cursor.execute("DELETE FROM Vehicle WHERE owner_id IN (SELECT owner_id FROM Owner WHERE user_id = %s)", (user_id,))
            # Delete owner record
            cursor.execute("DELETE FROM Owner WHERE user_id = %s", (user_id,))
        
        # Delete user record
        cursor.execute("DELETE FROM `User` WHERE user_id = %s", (user_id,))
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'msg': 'User deleted successfully'}), 200
        
    except Exception as e:
        if 'db' in locals() and db.is_connected():
            db.rollback()
            cursor.close()
            db.close()
        return jsonify({'error': str(e)}), 500

# Admin: enable/disable user
@app.route('/admin/users/<int:user_id>/status', methods=['PUT'])
def update_user_status(user_id):
    try:
        data = request.json or {}
        new_status = data.get("userStatus")
        if new_status not in ("active", "disabled"):
            return jsonify({'error': 'userStatus must be active or disabled'}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE `User` SET userStatus = %s, updateTime = %s WHERE user_id = %s", (new_status, datetime.now(), user_id))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'msg': 'User status updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin: export users CSV
@app.route('/admin/users.csv', methods=['GET'])
def export_users_csv():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT user_id, userType, userStatus, name, gmail, identityNo, address FROM `User` ORDER BY user_id")
        rows = cursor.fetchall()
        cursor.close()
        db.close()

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["user_id", "userType", "userStatus", "name", "gmail", "identityNo", "address"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

        return app.response_class(output.getvalue(), mimetype="text/csv; charset=utf-8")
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin: approve/deny owner
@app.route('/admin/owners/<int:owner_id>/verification', methods=['PUT'])
def update_owner_verification(owner_id):
    try:
        data = request.json or {}
        status = data.get("verificationStatus")
        if status not in ("pending", "approved", "rejected"):
            return jsonify({'error': 'verificationStatus must be pending/approved/rejected'}), 400
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE Owner SET verificationStatus = %s WHERE owner_id = %s", (status, owner_id))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'msg': 'Owner verification updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin: approve/deny vehicle
@app.route('/admin/vehicles/<int:vehicle_id>/verification', methods=['PUT'])
def update_vehicle_verification(vehicle_id):
    try:
        data = request.json or {}
        status = data.get("verificationStatus")
        if status not in ("pending", "approved", "rejected"):
            return jsonify({'error': 'verificationStatus must be pending/approved/rejected'}), 400
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE Vehicle SET verificationStatus = %s WHERE vehicle_id = %s", (status, vehicle_id))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'msg': 'Vehicle verification updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin: export vehicles CSV
@app.route('/admin/vehicles.csv', methods=['GET'])
def export_vehicles_csv():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.vehicle_id, v.owner_id, v.carType, v.lisenceNum, v.year, v.seatNum, v.status, v.dailyPrice, v.brand, v.model, v.location, v.verificationStatus
            FROM Vehicle v
            ORDER BY v.vehicle_id
        """)
        rows = cursor.fetchall()
        cursor.close()
        db.close()

        output = io.StringIO()
        fieldnames = ["vehicle_id", "owner_id", "carType", "lisenceNum", "year", "seatNum", "status", "dailyPrice", "brand", "model", "location", "verificationStatus"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

        return app.response_class(output.getvalue(), mimetype="text/csv; charset=utf-8")
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin: export rentals CSV
@app.route('/admin/rentals.csv', methods=['GET'])
def export_rentals_csv():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT rental_id, vehicle_id, renter_id, rentalStartTime, rentalEndTime, pickupLocation, dropoffLocation, totalAmount, orderStatus, paymentStatus, returnTime, dailyPrice, createTime, insurance_id
            FROM Rental
            ORDER BY rental_id
        """)
        rows = cursor.fetchall()
        cursor.close()
        db.close()

        output = io.StringIO()
        fieldnames = ["rental_id", "vehicle_id", "renter_id", "rentalStartTime", "rentalEndTime", "pickupLocation", "dropoffLocation", "totalAmount", "orderStatus", "paymentStatus", "returnTime", "dailyPrice", "createTime", "insurance_id"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

        return app.response_class(output.getvalue(), mimetype="text/csv; charset=utf-8")
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Owner: list vehicles
@app.route('/owner/<int:user_id>/vehicles', methods=['GET'])
def owner_list_vehicles(user_id):
    try:
        owner_id = _get_owner_id_for_user(user_id)
        if not owner_id:
            return jsonify({'error': 'Owner record not found'}), 404

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Vehicle WHERE owner_id = %s ORDER BY vehicle_id DESC", (owner_id,))
        vehicles = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(vehicles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Owner: create vehicle
@app.route('/owner/<int:user_id>/vehicles', methods=['POST'])
def owner_create_vehicle(user_id):
    try:
        owner_id = _get_owner_id_for_user(user_id)
        if not owner_id:
            return jsonify({'error': 'Owner record not found'}), 404

        data = request.json or {}
        required = ["carType", "lisenceNum", "year", "seatNum", "dailyPrice", "location"]
        for f in required:
            if f not in data or data[f] in (None, ""):
                return jsonify({'error': f'Missing required field: {f}'}), 400

        db = get_db()
        cursor = db.cursor()
        sql = """
            INSERT INTO Vehicle (owner_id, carType, lisenceNum, year, seatNum, status, photoURL, registerTime, dailyPrice, brand, model, location, description, verificationStatus)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            owner_id,
            data.get("carType"),
            data.get("lisenceNum"),
            int(data.get("year")),
            int(data.get("seatNum")),
            data.get("status", "available"),
            data.get("photoURL"),
            datetime.now(),
            float(data.get("dailyPrice")),
            data.get("brand"),
            data.get("model"),
            data.get("location"),
            data.get("description"),
            data.get("verificationStatus", "pending"),
        ))
        vehicle_id = cursor.lastrowid
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'msg': 'Vehicle created', 'vehicle_id': vehicle_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Owner: update vehicle
@app.route('/owner/<int:user_id>/vehicles/<int:vehicle_id>', methods=['PUT'])
def owner_update_vehicle(user_id, vehicle_id):
    try:
        owner_id = _get_owner_id_for_user(user_id)
        if not owner_id:
            return jsonify({'error': 'Owner record not found'}), 404

        data = request.json or {}
        allowed = ["carType", "lisenceNum", "year", "seatNum", "status", "photoURL", "dailyPrice", "brand", "model", "location", "description"]
        sets = []
        params = []
        for k in allowed:
            if k in data:
                sets.append(f"{k} = %s")
                params.append(data[k])
        if not sets:
            return jsonify({'error': 'No fields to update'}), 400

        params.extend([owner_id, vehicle_id])
        db = get_db()
        cursor = db.cursor()
        cursor.execute(f"UPDATE Vehicle SET {', '.join(sets)} WHERE owner_id = %s AND vehicle_id = %s", params)
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'msg': 'Vehicle updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Owner: list rentals for owned vehicles
@app.route('/owner/<int:user_id>/rentals', methods=['GET'])
def owner_list_rentals(user_id):
    try:
        owner_id = _get_owner_id_for_user(user_id)
        if not owner_id:
            return jsonify({'error': 'Owner record not found'}), 404

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.*, v.brand, v.model, v.carType, v.lisenceNum
            FROM Rental r
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
            WHERE v.owner_id = %s
            ORDER BY r.createTime DESC, r.rental_id DESC
        """, (owner_id,))
        rows = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Owner: monthly revenue (paid rentals)
@app.route('/owner/<int:user_id>/revenue', methods=['GET'])
def owner_monthly_revenue(user_id):
    try:
        owner_id = _get_owner_id_for_user(user_id)
        if not owner_id:
            return jsonify({'error': 'Owner record not found'}), 404

        months = int(request.args.get("months", "6"))
        months = max(1, min(months, 24))

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT DATE_FORMAT(r.createTime, '%Y-%m') as month,
                   COUNT(*) as order_count,
                   COALESCE(SUM(r.totalAmount), 0) as total_revenue
            FROM Rental r
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
            WHERE v.owner_id = %s AND r.paymentStatus = 'paid'
            GROUP BY DATE_FORMAT(r.createTime, '%Y-%m')
            ORDER BY month DESC
            LIMIT %s
        """, (owner_id, months))
        rows = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        if 'db' in locals() and db.is_connected():
            db.rollback()
            cursor.close()
            db.close()
        return jsonify({'error': str(e)}), 500

# Get All Vehicle Information
@app.route('/admin/vehicles', methods=['GET'])
def get_all_vehicles():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        status = request.args.get("status")
        verificationStatus = request.args.get("verificationStatus")
        owner_email = request.args.get("owner_gmail")

        where = []
        params = []
        if status:
            where.append("v.status = %s")
            params.append(status)
        if verificationStatus:
            where.append("v.verificationStatus = %s")
            params.append(verificationStatus)
        if owner_email:
            where.append("u.gmail LIKE %s")
            params.append(f"%{owner_email}%")

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        cursor.execute("""
            SELECT 
                v.*,
                u.name as owner_name,
                u.gmail as owner_email
            FROM Vehicle v
            JOIN Owner o ON v.owner_id = o.owner_id
            JOIN `User` u ON o.user_id = u.user_id
            {where_sql}
            ORDER BY v.vehicle_id
        """.format(where_sql=where_sql), params)
        
        vehicles = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(vehicles)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update Vehicle Status
@app.route('/admin/vehicles/<int:vehicle_id>/status', methods=['PUT'])
def update_vehicle_status(vehicle_id):
    try:
        data = request.json
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status cannot be empty'}), 400
        
        valid_statuses = ['available', 'rented', 'maintenance']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Status must be: {", ".join(valid_statuses)}'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("UPDATE Vehicle SET status = %s WHERE vehicle_id = %s", 
                      (new_status, vehicle_id))
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'msg': 'Vehicle status updated successfully'}), 200
        
    except Exception as e:
        if 'db' in locals() and db.is_connected():
            db.rollback()
            cursor.close()
            db.close()
        return jsonify({'error': str(e)}), 500

# Update Rental Order Information
@app.route('/admin/rentals/<int:rental_id>', methods=['PUT'])
def update_rental_order(rental_id):
    try:
        data = request.json
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # First check if order exists
        cursor.execute("SELECT * FROM Rental WHERE rental_id = %s", (rental_id,))
        rental = cursor.fetchone()
        
        if not rental:
            return jsonify({'error': 'Rental order does not exist'}), 404
        
        # Build update statement
        update_fields = []
        update_values = []
        
        if 'rentalStartTime' in data:
            update_fields.append("rentalStartTime = %s")
            update_values.append(data['rentalStartTime'])
        
        if 'rentalEndTime' in data:
            update_fields.append("rentalEndTime = %s")
            update_values.append(data['rentalEndTime'])
        
        if 'totalAmount' in data:
            update_fields.append("totalAmount = %s")
            update_values.append(float(data['totalAmount']))
        
        if 'orderStatus' in data:
            update_fields.append("orderStatus = %s")
            update_values.append(data['orderStatus'])
            
            # If status becomes completed, set return time
            if data['orderStatus'] == 'completed':
                update_fields.append("returnTime = %s")
                update_values.append(datetime.now().isoformat())
        
        if 'paymentStatus' in data:
            update_fields.append("paymentStatus = %s")
            update_values.append(data['paymentStatus'])
        
        if not update_fields:
            return jsonify({'error': 'No update fields provided'}), 400
        
        update_values.append(rental_id)
        
        sql = f"UPDATE Rental SET {', '.join(update_fields)} WHERE rental_id = %s"
        cursor.execute(sql, update_values)
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'msg': 'Rental order updated successfully'}), 200
        
    except Exception as e:
        if 'db' in locals() and db.is_connected():
            db.rollback()
            cursor.close()
            db.close()
        return jsonify({'error': str(e)}), 500
    
# Get Top 5 Most Rented Vehicles
@app.route('/admin/top-vehicles', methods=['GET'])
def get_top_vehicles():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                v.vehicle_id,
                v.brand,
                v.model,
                v.carType,
                v.dailyPrice,
                COUNT(r.rental_id) as rental_count,
                COALESCE(SUM(r.totalAmount), 0) as total_revenue
            FROM Vehicle v
            LEFT JOIN Rental r ON v.vehicle_id = r.vehicle_id
            GROUP BY v.vehicle_id, v.brand, v.model, v.carType, v.dailyPrice
            ORDER BY rental_count DESC, total_revenue DESC, v.vehicle_id
            LIMIT 5
        """)
        
        top_vehicles = cursor.fetchall()
        
        # Ensure correct data types
        for vehicle in top_vehicles:
            # Ensure dailyPrice is float
            if vehicle['dailyPrice'] is not None:
                vehicle['dailyPrice'] = float(vehicle['dailyPrice'])
            else:
                vehicle['dailyPrice'] = 0.0
                
            # Ensure rental_count is integer
            vehicle['rental_count'] = int(vehicle['rental_count'])
            
            # Ensure total_revenue is float
            vehicle['total_revenue'] = float(vehicle['total_revenue'])
        
        cursor.close()
        db.close()
        
        return jsonify(top_vehicles)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Monthly Revenue Statistics
@app.route('/admin/monthly-revenue', methods=['GET'])
def get_monthly_revenue():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                DATE_FORMAT(rentalStartTime, '%Y-%m') as month,
                COUNT(*) as order_count,
                SUM(totalAmount) as total_revenue
            FROM Rental 
            WHERE paymentStatus = 'paid'
            GROUP BY DATE_FORMAT(rentalStartTime, '%Y-%m')
            ORDER BY month DESC
            LIMIT 6
        """)
        
        monthly_data = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(monthly_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Order Status Distribution
@app.route('/admin/order-status-stats', methods=['GET'])
def get_order_status_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                orderStatus,
                COUNT(*) as count
            FROM Rental 
            GROUP BY orderStatus
        """)
        
        status_stats = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(status_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Detailed Rental Order Information
@app.route('/admin/rental/<int:rental_id>/details', methods=['GET'])
def get_rental_details(rental_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                r.rental_id,
                r.rentalStartTime,
                r.rentalEndTime,
                r.totalAmount,
                r.orderStatus,
                r.paymentStatus,
                r.returnTime,
                v.vehicle_id,
                v.brand,
                v.model,
                v.carType,
                v.year,
                v.color,
                v.dailyPrice,
                v.status as vehicle_status,
                u.user_id as renter_user_id,
                u.name as renter_name,
                u.gmail as renter_email,
                u.identityNo as renter_identity,
                u.address as renter_address,
                i.insurance_id,
                i.types as insurance_type,
                i.coverage as insurance_coverage,
                i.fee as insurance_fee,
                p.paymentMethod,
                p.paymentTime,
                p.TransactionNumber,
                o.user_id as owner_user_id,
                owner_user.name as owner_name,
                owner_user.gmail as owner_email
            FROM Rental r
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
            JOIN Renter rt ON r.renter_id = rt.renter_id
            JOIN `User` u ON rt.user_id = u.user_id
            JOIN Owner o ON v.owner_id = o.owner_id
            JOIN `User` owner_user ON o.user_id = owner_user.user_id
            LEFT JOIN Insurance i ON r.insurance_id = i.insurance_id
            LEFT JOIN Payment p ON r.rental_id = p.rental_id
            WHERE r.rental_id = %s
        """, (rental_id,))
        
        rental_details = cursor.fetchone()
        cursor.close()
        db.close()
        
        if rental_details:
            return jsonify(rental_details)
        else:
            return jsonify({'error': 'Rental order does not exist'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Platform Statistics
@app.route('/admin/stats', methods=['GET'])
def get_admin_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Get total orders
        cursor.execute("SELECT COUNT(*) as total_orders FROM Rental")
        total_orders = cursor.fetchone()['total_orders']
        
        # Get today's orders
        cursor.execute("SELECT COUNT(*) as today_orders FROM Rental WHERE DATE(createTime) = CURDATE()")
        today_orders = cursor.fetchone()['today_orders']
        
        # Get total revenue
        cursor.execute("SELECT SUM(totalAmount) as total_revenue FROM Rental WHERE paymentStatus = 'paid'")
        total_revenue_result = cursor.fetchone()
        total_revenue = total_revenue_result['total_revenue'] if total_revenue_result['total_revenue'] else 0
        
        # Get total users
        cursor.execute("SELECT COUNT(*) as total_users FROM `User`")
        total_users = cursor.fetchone()['total_users']
        
        # Get active orders
        cursor.execute("SELECT COUNT(*) as active_orders FROM Rental WHERE orderStatus IN ('confirmed', 'active')")
        active_orders = cursor.fetchone()['active_orders']
        
        # Get available vehicles
        cursor.execute("SELECT COUNT(*) as available_vehicles FROM Vehicle WHERE status = 'available'")
        available_vehicles = cursor.fetchone()['available_vehicles']
        
        cursor.close()
        db.close()
        
        return jsonify({
            'total_orders': total_orders,
            'today_orders': today_orders,
            'total_revenue': float(total_revenue),
            'total_users': total_users,
            'active_orders': active_orders,
            'available_vehicles': available_vehicles
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get All Rental Orders (for admin)
@app.route('/admin/rentals', methods=['GET'])
def get_all_rentals():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        orderStatus = request.args.get("orderStatus")
        paymentStatus = request.args.get("paymentStatus")
        renter_gmail = request.args.get("renter_gmail")

        where = []
        params = []
        if orderStatus:
            where.append("r.orderStatus = %s")
            params.append(orderStatus)
        if paymentStatus:
            where.append("r.paymentStatus = %s")
            params.append(paymentStatus)
        if renter_gmail:
            where.append("u.gmail LIKE %s")
            params.append(f"%{renter_gmail}%")

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        cursor.execute("""
            SELECT 
                r.rental_id,
                r.rentalStartTime,
                r.rentalEndTime,
                r.totalAmount,
                r.orderStatus,
                r.paymentStatus,
                r.returnTime,
                r.createTime,
                v.vehicle_id,
                v.brand,
                v.model,
                v.carType,
                v.dailyPrice,
                u.user_id as renter_user_id,
                u.name as renter_name,
                u.gmail as renter_email
            FROM Rental r
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
            JOIN Renter rt ON r.renter_id = rt.renter_id
            JOIN `User` u ON rt.user_id = u.user_id
            {where_sql}
            ORDER BY r.rental_id DESC
        """.format(where_sql=where_sql), params)
        
        rentals = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(rentals)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update Rental Order Status
@app.route('/admin/rentals/<int:rental_id>/status', methods=['PUT'])
def update_rental_status(rental_id):
    try:
        data = request.json
        new_status = data.get('orderStatus')
        
        if not new_status:
            return jsonify({'error': 'Status cannot be empty'}), 400
        
        valid_statuses = ['pending', 'confirmed', 'active', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Status must be: {", ".join(valid_statuses)}'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Update order status
        cursor.execute("UPDATE Rental SET orderStatus = %s WHERE rental_id = %s", 
                      (new_status, rental_id))
        
        # If status becomes completed, set return time
        if new_status == 'completed':
            cursor.execute("UPDATE Rental SET returnTime = %s WHERE rental_id = %s", 
                          (datetime.now(), rental_id))
            
            # Also update vehicle status to available
            cursor.execute("""
                UPDATE Vehicle v 
                JOIN Rental r ON v.vehicle_id = r.vehicle_id 
                SET v.status = 'available' 
                WHERE r.rental_id = %s
            """, (rental_id,))
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'msg': 'Order status updated successfully'}), 200
        
    except Exception as e:
        if 'db' in locals() and db.is_connected():
            db.rollback()
            cursor.close()
            db.close()
        return jsonify({'error': str(e)}), 500

# Get Monthly Statistics (for charts)
@app.route('/admin/monthly-stats', methods=['GET'])
def get_monthly_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                DATE_FORMAT(rentalStartTime, '%Y-%m') as month,
                COUNT(*) as order_count,
                SUM(totalAmount) as total_revenue
            FROM Rental 
            WHERE paymentStatus = 'paid'
            GROUP BY DATE_FORMAT(rentalStartTime, '%Y-%m')
            ORDER BY month DESC
            LIMIT 6
        """)
        
        monthly_data = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(monthly_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Vehicle Type Distribution Statistics
@app.route('/admin/vehicle-type-stats', methods=['GET'])
def get_vehicle_type_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                carType,
                COUNT(*) as count
            FROM Vehicle 
            GROUP BY carType
            ORDER BY count DESC
        """)
        
        type_stats = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(type_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get User Type Distribution Statistics
@app.route('/admin/user-type-stats', methods=['GET'])
def get_user_type_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                userType,
                COUNT(*) as count
            FROM `User` 
            WHERE userType != 'admin'  -- Exclude admin
            GROUP BY userType
            ORDER BY count DESC
        """)
        
        type_stats = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(type_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Yearly Revenue Trend Data
@app.route('/admin/yearly-revenue', methods=['GET'])
def get_yearly_revenue():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                YEAR(rentalStartTime) as year,
                MONTH(rentalStartTime) as month,
                SUM(totalAmount) as monthly_revenue
            FROM Rental 
            WHERE paymentStatus = 'paid'
            GROUP BY YEAR(rentalStartTime), MONTH(rentalStartTime)
            ORDER BY year, month
        """)
        
        yearly_data = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(yearly_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Rental Duration Distribution Statistics
@app.route('/admin/rental-duration-stats', methods=['GET'])
def get_rental_duration_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN DATEDIFF(rentalEndTime, rentalStartTime) <= 1 THEN '1 day'
                    WHEN DATEDIFF(rentalEndTime, rentalStartTime) <= 3 THEN '2-3 days'
                    WHEN DATEDIFF(rentalEndTime, rentalStartTime) <= 7 THEN '4-7 days'
                    ELSE '7+ days'
                END as duration_range,
                COUNT(*) as count
            FROM Rental 
            WHERE rentalStartTime IS NOT NULL AND rentalEndTime IS NOT NULL
            GROUP BY duration_range
            ORDER BY 
                CASE duration_range
                    WHEN '1 day' THEN 1
                    WHEN '2-3 days' THEN 2
                    WHEN '4-7 days' THEN 3
                    ELSE 4
                END
        """)
        
        duration_stats = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(duration_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Vehicle Brand Distribution Statistics
@app.route('/admin/vehicle-brand-stats', methods=['GET'])
def get_vehicle_brand_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                brand,
                COUNT(*) as count
            FROM Vehicle 
            GROUP BY brand
            ORDER BY count DESC
            LIMIT 10  -- Show only top 10 brands
        """)
        
        brand_stats = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(brand_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Owner Rating Distribution
@app.route('/admin/owner-rating-stats', methods=['GET'])
def get_owner_rating_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN rating >= 4.5 THEN '4.5-5.0'
                    WHEN rating >= 4.0 THEN '4.0-4.4'
                    WHEN rating >= 3.5 THEN '3.5-3.9'
                    WHEN rating >= 3.0 THEN '3.0-3.4'
                    ELSE 'Below 3.0'
                END as rating_range,
                COUNT(*) as count
            FROM Owner 
            WHERE rating IS NOT NULL
            GROUP BY rating_range
            ORDER BY 
                CASE rating_range
                    WHEN '4.5-5.0' THEN 1
                    WHEN '4.0-4.4' THEN 2
                    WHEN '3.5-3.9' THEN 3
                    WHEN '3.0-3.4' THEN 4
                    ELSE 5
                END
        """)
        
        rating_stats = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(rating_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Renter Rating Distribution
@app.route('/admin/renter-rating-stats', methods=['GET'])
def get_renter_rating_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN rating >= 4.5 THEN '4.5-5.0'
                    WHEN rating >= 4.0 THEN '4.0-4.4'
                    WHEN rating >= 3.5 THEN '3.5-3.9'
                    WHEN rating >= 3.0 THEN '3.0-3.4'
                    ELSE 'Below 3.0'
                END as rating_range,
                COUNT(*) as count
            FROM Renter 
            WHERE rating IS NOT NULL
            GROUP BY rating_range
            ORDER BY 
                CASE rating_range
                    WHEN '4.5-5.0' THEN 1
                    WHEN '4.0-4.4' THEN 2
                    WHEN '3.5-3.9' THEN 3
                    WHEN '3.0-3.4' THEN 4
                    ELSE 5
                END
        """)
        
        rating_stats = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(rating_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Payment Method Distribution
@app.route('/admin/payment-method-stats', methods=['GET'])
def get_payment_method_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                paymentMethod,
                COUNT(*) as count,
                SUM(paymentAmount) as total_amount
            FROM Payment 
            WHERE paymentMethod IS NOT NULL
            GROUP BY paymentMethod
            ORDER BY count DESC
        """)
        
        payment_stats = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(payment_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Insurance Type Usage Statistics
@app.route('/admin/insurance-usage-stats', methods=['GET'])
def get_insurance_usage_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                i.types as insurance_type,
                COUNT(r.rental_id) as usage_count,
                SUM(i.fee) as total_fee
            FROM Insurance i
            LEFT JOIN Rental r ON i.insurance_id = r.insurance_id
            GROUP BY i.insurance_id, i.types
            ORDER BY usage_count DESC
        """)
        
        insurance_stats = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(insurance_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Vehicle Status Distribution
@app.route('/admin/vehicle-status-stats', methods=['GET'])
def get_vehicle_status_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM Vehicle 
            GROUP BY status
            ORDER BY count DESC
        """)
        
        status_stats = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(status_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)