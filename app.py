from flask import Flask, render_template, send_file
import qrcode, io

app = Flask(__name__)
table_status = {1:"Available",2:"Available",3:"Booked",4:"Available",5:"Booked",6:"Available"}

@app.route('/')
def home():
    return render_template('index.html', status=table_status)

@app.route('/qr/<int:table_id>')
def qr(table_id):
    # QR banane ka code
    url = f"http://127.0.0.1:5000/login/{table_id}"
    img = qrcode.make(url)
    b = io.BytesIO()
    img.save(b, 'PNG')
    b.seek(0)
    return send_file(b, mimetype='image/png')

@app.route('/login/<int:table_id>')
def login(table_id):
    return f"<h1>Table {table_id} Login OK - QR Working!</h1><a href='/'>Back</a>"

if __name__ == '__main__':
    app.run(debug=True)