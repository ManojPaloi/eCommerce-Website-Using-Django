import qrcode
import base64
from io import BytesIO

def generate_order_qr_code(order):
    data = f"Order ID: {order.id}\nName: {order.first_name} {order.last_name}\nTotal: ₹{order.total}"
    qr = qrcode.make(data)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str
