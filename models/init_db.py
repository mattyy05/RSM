#!/usr/bin/env python3
"""
Database Initialization Script
Populates the retail store database with sample data for testing
"""

from .database import Database

def init_sample_data():
    """Initialize the database with sample data"""
    db = Database()
    
    print("Initializing database with sample data...")
    
    # Categories will be added manually by the user
    # No default categories will be created
    electronics_id = None
    clothing_id = None
    books_id = None
    home_id = None
    
    # Add sample suppliers
    print("Adding suppliers...")
    supplier1_id = db.add_supplier(
        name="Tech Solutions Inc.",
        contact_person="John Smith",
        email="john@techsolutions.com",
        phone="123-456-7890",
        address="123 Tech Street, Tech City"
    )
    
    supplier2_id = db.add_supplier(
        name="Fashion Wholesale",
        contact_person="Sarah Johnson",
        email="sarah@fashionwholesale.com",
        phone="987-654-3210",
        address="456 Fashion Ave, Style City"
    )
    
    # Add sample customers
    print("Adding customers...")
    customer1_id = db.add_customer(
        name="Alice Brown",
        email="alice@email.com",
        phone="555-0101",
        address="789 Customer Lane, Buyer City",
        credit_limit=5000
    )
    
    customer2_id = db.add_customer(
        name="Bob Wilson",
        email="bob@email.com",
        phone="555-0102",
        address="321 Shopper St, Purchase Town",
        credit_limit=3000
    )
    
    # Add sample products
    print("Adding products...")
    products = [
        # Electronics
        {
            "name": "iPhone 15",
            "category_id": electronics_id,
            "cost_price": 800.00,
            "selling_price": 1000.00,
            "quantity": 25,
            "sku": "IPH15-001",
            "description": "Latest iPhone model with advanced features",
            "supplier": "Tech Solutions Inc."
        },
        {
            "name": "Samsung Galaxy S24",
            "category_id": electronics_id,
            "cost_price": 700.00,
            "selling_price": 900.00,
            "quantity": 30,
            "sku": "SAM24-001",
            "description": "Premium Android smartphone",
            "supplier": "Tech Solutions Inc."
        },
        {
            "name": "Wireless Headphones",
            "category_id": electronics_id,
            "cost_price": 50.00,
            "selling_price": 80.00,
            "quantity": 50,
            "sku": "WH-001",
            "description": "Bluetooth wireless headphones",
            "supplier": "Tech Solutions Inc."
        },
        
        # Clothing
        {
            "name": "Levi's Jeans",
            "category_id": clothing_id,
            "cost_price": 40.00,
            "selling_price": 70.00,
            "quantity": 75,
            "sku": "LJ-001",
            "description": "Classic blue jeans",
            "supplier": "Fashion Wholesale"
        },
        {
            "name": "Nike T-Shirt",
            "category_id": clothing_id,
            "cost_price": 15.00,
            "selling_price": 30.00,
            "quantity": 100,
            "sku": "NT-001",
            "description": "Cotton sports t-shirt",
            "supplier": "Fashion Wholesale"
        },
        
        # Books
        {
            "name": "Python Programming Book",
            "category_id": books_id,
            "cost_price": 25.00,
            "selling_price": 45.00,
            "quantity": 20,
            "sku": "PPB-001",
            "description": "Learn Python programming",
            "supplier": "Book Distributors"
        },
        
        # Home & Garden
        {
            "name": "Garden Tools Set",
            "category_id": home_id,
            "cost_price": 35.00,
            "selling_price": 60.00,
            "quantity": 15,
            "sku": "GTS-001",
            "description": "Complete garden tools set",
            "supplier": "Garden Supply Co."
        }
    ]
    
    product_ids = []
    for product in products:
        product_id = db.add_product(**product)
        if product_id:
            product_ids.append(product_id)
    
    # Add sample purchases
    print("Adding sample purchases...")
    # Purchase 1: Cash purchase
    purchase_items = [
        {"product_id": product_ids[0], "quantity": 10, "unit_cost": 800.00},
        {"product_id": product_ids[1], "quantity": 15, "unit_cost": 700.00}
    ]
    db.create_purchase(
        items=purchase_items,
        supplier_id=supplier1_id,
        payment_type='cash',
        reference_no="PO-001"
    )
    
    # Purchase 2: Credit purchase
    purchase_items = [
        {"product_id": product_ids[3], "quantity": 50, "unit_cost": 40.00},
        {"product_id": product_ids[4], "quantity": 75, "unit_cost": 15.00}
    ]
    db.create_purchase(
        items=purchase_items,
        supplier_id=supplier2_id,
        payment_type='credit',
        reference_no="PO-002"
    )
    
    # Add sample sales
    print("Adding sample sales...")
    # Sale 1: Cash sale
    sale_items = [
        {"product_id": product_ids[0], "quantity": 2, "unit_price": 1000.00},
        {"product_id": product_ids[2], "quantity": 3, "unit_price": 80.00}
    ]
    db.create_sale(
        items=sale_items,
        customer_id=None,  # Walk-in customer
        payment_type='cash',
        reference_no="SALE-001"
    )
    
    # Sale 2: Credit sale
    sale_items = [
        {"product_id": product_ids[3], "quantity": 5, "unit_price": 70.00},
        {"product_id": product_ids[4], "quantity": 10, "unit_price": 30.00}
    ]
    db.create_sale(
        items=sale_items,
        customer_id=customer1_id,
        payment_type='credit',
        reference_no="SALE-002"
    )
    
    # Add some cash transactions
    print("Adding sample cash transactions...")
    # Investment
    db.add_cash_in("Investment", 50000, "Initial capital investment", "INV-001")
    
    # Operating expenses
    db.add_cash_out("Expenses", 2000, "Office rent payment", "EXP-001")
    db.add_cash_out("Expenses", 500, "Utilities payment", "EXP-002")
    
    # Inventory adjustments
    print("Adding inventory adjustments...")
    db.add_inventory_adjustment(
        product_id=product_ids[2], 
        adjustment_type='decrease', 
        quantity=2, 
        reason="Damaged items", 
        reference_no="ADJ-001"
    )
    
    # Sample journal entries
    print("Adding sample journal entries...")
    # Cash receipt journal entry
    cash_receipt_lines = [
        {"account_name": "Cash", "debit_amount": 1000, "credit_amount": 0},
        {"account_name": "Sales Revenue", "debit_amount": 0, "credit_amount": 1000}
    ]
    db.create_journal_entry(
        journal_type="cash_receipt",
        lines=cash_receipt_lines,
        reference_no="CR-001",
        description="Cash sale recorded"
    )
    
    # Cash disbursement journal entry
    cash_disbursement_lines = [
        {"account_name": "Operating Expenses", "debit_amount": 500, "credit_amount": 0},
        {"account_name": "Cash", "debit_amount": 0, "credit_amount": 500}
    ]
    db.create_journal_entry(
        journal_type="cash_disbursement",
        lines=cash_disbursement_lines,
        reference_no="CD-001",
        description="Office rent payment"
    )
    
    print("Sample data initialization completed!")
    
    # Display summary
    print("\n=== DATABASE SUMMARY ===")
    print(f"Categories: {len(db.get_categories())}")
    print(f"Products: {len(db.get_products())}")
    print(f"Customers: {len(db.get_customers())}")
    print(f"Suppliers: {len(db.get_suppliers())}")
    
    # Cash flow summary
    cash_flow = db.get_cash_flow_summary()
    print(f"\nCash Flow Summary:")
    print(f"Total Cash In: ₱{cash_flow['total_cash_in']:,.2f}")
    print(f"Total Cash Out: ₱{cash_flow['total_cash_out']:,.2f}")
    print(f"Net Cash Flow: ₱{cash_flow['net_cash_flow']:,.2f}")
    
    # Sales summary
    sales_summary = db.get_sales_summary()
    print(f"\nSales Summary:")
    print(f"Total Sales: {sales_summary['total_sales']}")
    print(f"Total Revenue: ₱{sales_summary['total_revenue']:,.2f}")
    
    # Inventory value
    inventory_value = db.get_inventory_value()
    print(f"\nInventory Value: ₱{inventory_value:,.2f}")
    
    # Low stock products
    low_stock = db.get_low_stock_products()
    if low_stock:
        print(f"\nLow Stock Alert: {len(low_stock)} products need restocking")
    
    db.close()

if __name__ == "__main__":
    init_sample_data()
