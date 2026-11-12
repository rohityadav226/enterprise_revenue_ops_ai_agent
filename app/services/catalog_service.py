from app.data.mock_data import customers, products

def get_customer_by_id(customer_id):
    return customers.get(customer_id)

def get_product_by_id(product_id):
    return next((item for item in products if item["product_id"] == product_id), None)