# orders/utils.py
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_invoice_pdf(order, order_items, qr_code_data=None):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x_margin, y = 50, height - 50

    def draw_text(label, value):
        nonlocal y
        p.drawString(x_margin, y, f"{label}: {value}")
        y -= 15

    p.setFont("Helvetica-Bold", 16)
    p.drawString(x_margin, y, f"Invoice #{order.id}")
    y -= 25
    p.setFont("Helvetica", 12)
    draw_text("Order Date", order.created_at.strftime('%B %d, %Y, %I:%M %p'))
    draw_text("Order Status", order.order_status.title())
    draw_text("Name", f"{order.first_name} {order.last_name}")
    draw_text("Email", order.email)
    draw_text("Phone", f"{order.country_code}{order.phone}")
    draw_text("Billing Address", f"{order.street} {order.building or ''} {order.house or ''}, {order.city}, {order.state}, {order.postal_code} {order.zip_code}, {order.country}")

    if order.shipping_first_name:
        draw_text("Shipping Name", f"{order.shipping_first_name} {order.shipping_last_name}")
        draw_text("Shipping Phone", f"{order.shipping_country_code}{order.shipping_phone}")
        draw_text("Shipping Address", f"{order.shipping_street} {order.shipping_building or ''} {order.shipping_house or ''}, {order.shipping_city}, {order.shipping_state}, {order.shipping_postal_code} {order.shipping_zip_code}, {order.shipping_country}")
    else:
        draw_text("Shipping", "Same as billing address")

    draw_text("Payment Method", order.payment_method.title())
    draw_text("Payment Status", order.payment_status.title())
    draw_text("Paid Online", "Yes" if order.is_paid_online else "No")

    if order.razorpay_payment_id:
        draw_text("Transaction ID", order.razorpay_payment_id)
    if order.coupon_code:
        draw_text("Coupon Code", order.coupon_code)

    draw_text("Delivery Slot", order.get_delivery_slot_display())
    draw_text("Express Delivery", "Yes" if order.express_delivery else "No")
    draw_text("Expected Delivery", order.expected_delivery_date.strftime('%B %d, %Y'))

    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x_margin, y, "Products:")
    y -= 20

    p.setFont("Helvetica-Bold", 11)
    p.drawString(x_margin, y, "Product")
    p.drawString(x_margin + 250, y, "Qty")
    p.drawString(x_margin + 300, y, "Unit Price")
    p.drawString(x_margin + 400, y, "Total")
    y -= 15
    p.setFont("Helvetica", 11)

    for item in order_items:
        p.drawString(x_margin, y, item.product_name[:35])
        p.drawString(x_margin + 250, y, str(item.quantity))
        p.drawString(x_margin + 300, y, f"₹{item.price:.2f}")
        p.drawString(x_margin + 400, y, f"₹{item.total_price:.2f}")
        y -= 15
        if y < 100:
            p.showPage()
            y = height - 50

    y -= 10
    p.drawString(x_margin + 300, y, "Subtotal:")
    p.drawString(x_margin + 400, y, f"₹{order.subtotal:.2f}")
    y -= 15
    p.drawString(x_margin + 300, y, "Tax (18%):")
    p.drawString(x_margin + 400, y, f"₹{order.tax:.2f}")
    y -= 15
    p.drawString(x_margin + 300, y, "Delivery:")
    p.drawString(x_margin + 400, y, f"₹{order.delivery_charge:.2f}")
    y -= 15
    p.drawString(x_margin + 300, y, "Discount:")
    p.drawString(x_margin + 400, y, f"-₹{order.discount:.2f}")
    y -= 15
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x_margin + 300, y, "Grand Total:")
    p.drawString(x_margin + 400, y, f"₹{order.total:.2f}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer
