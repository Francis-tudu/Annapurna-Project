from flask import Flask, render_template, request, redirect, send_file
import socket
import qrcode, io, base64

app = Flask(__name__)

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

table_status = {
    "1": {"type": "Silver", "status": "available", "price": 100},
    "2": {"type": "Gold", "status": "available", "price": 200},
    "3": {"type": "Platinum", "status": "available", "price": 300}
}

kitchen_orders = []
feedbacks = []

def make_qr_base64(data):
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/booking')
def booking():
    return render_template('booking.html', table_status=table_status)

@app.route('/kitchen')
def kitchen():
    return render_template('kitchen.html', orders=kitchen_orders)

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/admin_analytics')
def admin_analytics():
    return render_template('admin.html')

@app.route('/login/<table_id>', methods=['GET', 'POST'])
def login_table(table_id):
    if request.method == 'POST':
        table_status[table_id]['status'] = 'booked'
        return redirect(f'/menu/{table_id}')
    return render_template('login.html', table_id=table_id)

@app.route('/menu/<table_id>')
def menu_table(table_id):
    items = [
        {"name": "Paneer Butter Masala", "base": 60, "img": "🍛"},
        {"name": "Biryani", "base": 80, "img": "🍚"},
        {"name": "Chicken Curry", "base": 70, "img": "🍗"},
        {"name": "Dal Tadka", "base": 75, "img": "🥘"},
        {"name": "Butter Naan", "base": 50, "img": "🫓"},
        {"name": "Cold Drink", "base": 40, "img": "🥤"}
    ]
    table_num = int(table_id)
    if table_num == 1: tier = {"name": "Silver", "table_price": 100, "factor": 1}
    elif table_num == 2: tier = {"name": "Gold", "table_price": 200, "factor": 1.5}
    else: tier = {"name": "Platinum", "table_price": 300, "factor": 2}
    
    menu_items = []
    for it in items:
        menu_items.append({"name": it["name"], "price": int(it["base"]*tier["factor"]), "img": it["img"], "base": it["base"]})
    return render_template('menu.html', table=table_id, tier=tier, items=menu_items)

@app.route('/qr/<table_id>')
def qr_table(table_id):
    my_ip = get_my_ip()
    menu_url = f"http://{my_ip}:5000/menu/{table_id}"
    qr_img = make_qr_base64(menu_url)
    return f'<div style="text-align:center;padding:20px"><h1>Table {table_id}</h1><h3>Scan to Order</h3><img src="data:image/png;base64,{qr_img}" style="width:300px"><p>{menu_url}</p><a href="/qr_all">Back</a></div>'

# NEW ROUTE FOR ADMIN QR - THIS WAS MISSING
@app.route('/qr_img/<table_id>')
def qr_img(table_id):
    my_ip = get_my_ip()
    menu_url = f"http://{my_ip}:5000/menu/{table_id}"
    img = qrcode.make(menu_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/qr_all')
def qr_all():
    my_ip = get_my_ip()
    html = "<h1 style='text-align:center;'>Annapurna - All Table QR</h1><div style='display:flex;flex-wrap:wrap;justify-content:center;'>"
    for i in ["1","2","3"]:
        link = f"http://{my_ip}:5000/menu/{i}"
        qr_img_b64 = make_qr_base64(link)
        html += f"<div style='margin:10px;text-align:center;border:1px solid #ccc;padding:10px;border-radius:10px'><h3>Table {i}</h3><img src='data:image/png;base64,{qr_img_b64}' style='width:200px'><br><small>{link}</small></div>"
    html += "</div><div style='text-align:center;margin-top:20px'><a href='/admin'>Back to Admin</a></div>"
    return html

@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.get_json()
    table = data.get('table')
    cart = data.get('cart')
    for item in cart:
        kitchen_orders.append({"table": f"Table {table}", "item": item['name'], "name": item['name'], "price": item.get('price', 0), "status": "Cooking", "table_id": str(table)})
    return {"status": "success"}

@app.route('/billing')
def billing_list():
    return render_template('billing_list.html', tables=table_status)

@app.route('/billing/<table_id>')
def billing_table(table_id):
    table_orders = [o for o in kitchen_orders if o.get('table_id') == str(table_id)]
    total = sum([o.get('price', 0) for o in table_orders])
    table_charge = table_status[table_id]['price']
    grand = total + table_charge
    return render_template('billing.html', table=table_id, orders=table_orders, total=total, table_charge=table_charge, grand=grand)

@app.route('/bill/<table_id>')
def bill_table(table_id):
    global kitchen_orders
    table_status[table_id]['status'] = 'available'
    kitchen_orders = [o for o in kitchen_orders if o.get('table_id') != str(table_id)]
    return f"<h1>Bill Paid! Table {table_id} Free!</h1><a href='/admin'>Admin</a>"

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        feedbacks.append(request.form)
        return "<h1>Thank You!</h1><a href='/'>Home</a>"
    return render_template('feedback.html')

if __name__ == '__main__':
    print("Your IP:", get_my_ip())
    app.run(host='0.0.0.0', port=5000, debug=True)
