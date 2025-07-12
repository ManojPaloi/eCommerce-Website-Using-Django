import io
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from xhtml2pdf import pisa
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.template.loader import get_template
from django.template.loader import render_to_string


from .models import Order

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Invoice for Order #{order.id}")

    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Name: {order.first_name} {order.last_name}")
    p.drawString(50, height - 100, f"Email: {order.email}")
    p.drawString(50, height - 120, f"Phone: {order.country_code}{order.phone}")

    p.drawString(50, height - 150, "Address:")
    p.drawString(70, height - 170, f"{order.street} {order.building} {order.house}")
    p.drawString(70, height - 190, f"{order.city}, {order.state}")
    p.drawString(70, height - 210, f"{order.postal_code} {order.zip_code}")
    p.drawString(70, height - 230, order.country)

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 270, "Product")
    p.drawString(300, height - 270, "Qty")
    p.drawString(350, height - 270, "Unit Price")
    p.drawString(450, height - 270, "Total")

    y = height - 290
    p.setFont("Helvetica", 12)

    for item in order.items.all():
        p.drawString(50, y, item.product_name[:40])
        p.drawString(300, y, str(item.quantity))
        p.drawString(350, y, f"₹{item.price}")
        p.drawString(450, y, f"₹{item.total_price}")
        y -= 20
        if y < 50:
            p.showPage()
            y = height - 50

    y -= 20
    p.drawString(350, y, "Subtotal:")
    p.drawString(450, y, f"₹{order.subtotal}")
    y -= 20
    p.drawString(350, y, "Delivery Charge:")
    p.drawString(450, y, f"₹{order.delivery_charge}")
    y -= 20
    p.drawString(350, y, "Discount:")
    p.drawString(450, y, f"-₹{order.discount}")
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(350, y, "Grand Total:")
    p.drawString(450, y, f"₹{order.total}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"Invoice_Order_{order.id}.pdf")




@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    download_invoice = request.GET.get('download_invoice', False)
    
    if download_invoice:
        template_name = 'store/track_order_invoice.html'  # no header/footer here
    else:
        template_name = 'store/track_order.html'  # full page with header/footer

    return render(request, template_name, {'order': order})






@login_required
def download_invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {'order': order, 'order_items': order.items.all()}
    html = render_to_string('store/order_invoice_pdf.html', context)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode('utf-8')), result)
    if not pdf.err:
        result.seek(0)
        return FileResponse(result, as_attachment=True, filename=f'Invoice_{order.id}.pdf')
    return HttpResponse('Error generating PDF', status=500)



