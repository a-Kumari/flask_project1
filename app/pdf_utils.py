from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import datetime
import os
from flask_mail import Message
from app import  mail


def generate_receipt_pdf(orders, buyer_id, receipt_id):
    # Use user's home directory to ensure accessibility

    directory ="receipts"

    # Create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Generate the filename and path
    pdf_path = os.path.join(directory, f"receipt_{receipt_id}.pdf")
    
    # Create the PDF canvas
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    # Add basic receipt information
    c.drawString(100, 750, "Order Receipt")
    c.drawString(100, 730, f"Receipt ID: {receipt_id}")
    c.drawString(100, 710, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(100, 690, f"Buyer ID: {buyer_id}")
    
    # Convert orders to list if it's a single dictionary
    if isinstance(orders, dict):
        orders = [orders]

    # Add order details
    y = 650
    total_final_amount = 0
    for order in orders:
        product_id = order['product_id']
        quantity = order['quantity']
        price = order['price']
        total_price = order['total_price']
        discount_applied = order['discount_applied']
    
        # Add each product detail to the PDF
        c.drawString(100, y, f"Product ID: {product_id} - Quantity: {quantity} - Price: {price} - Total Price: {total_price} - Discount: {discount_applied}%")
        y -= 20
        total_final_amount += total_price

    # Add the total final amount at the end
    c.drawString(100, y - 20, f"Total Final Amount: {total_final_amount}")
    
    # Save the PDF
    c.save()

    return pdf_path

def send_invoice_email_with_pdf(email, receipt_id, pdf_path):
    # Create the message
    msg = Message(
        subject=f"Your Invoice #{receipt_id}",
        recipients=[email],
        body=f"Dear customer,\n\nPlease find attached your invoice #{receipt_id} for your recent order."
    )

    # Check if the PDF exists
    if os.path.exists(pdf_path):
        try:
            with open(pdf_path, 'rb') as attachment:
                msg.attach(
                    filename=os.path.basename(pdf_path),
                    content_type='application/pdf',
                    data=attachment.read()
                )
        except Exception as e:
            print(f"Error reading the file: {e}")
            return
    else:
        print(f"Error: invoice file not found at path {pdf_path}")
        return

    # Try sending the email
    try:
        mail.send(msg)
        print(f"Invoice email sent successfully to {email}")
    except Exception as e:
        print(f"Error sending email: {e}")
