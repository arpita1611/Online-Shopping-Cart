# -------------------- ONLINE SHOPPING CART --------------------

import json
import os       

# -------------------- Product base class --------------------

class Product:
    def __init__(self, product_id, name, price, quantity_available):
        self._product_id = product_id
        self._name = name
        self._price = price
        self._quantity_available = quantity_available

    @property
    def product_id(self): return self._product_id
    @property
    def name(self): return self._name
    @property
    def price(self): return self._price
    @property
    def quantity_available(self): return self._quantity_available

    @quantity_available.setter
    def quantity_available(self, value):
        if value < 0:
            raise ValueError("Quantity cannot be negative.")
        self._quantity_available = value

    def decrease_quantity(self, amount):
        if amount <= self._quantity_available:
            self._quantity_available -= amount
            return True
        return False

    def increase_quantity(self, amount):
        self._quantity_available += amount

    def display_details(self):
        return f"ID: {self.product_id} | Name: {self.name} | Price: ₹{self.price:.2f} | Stock: {self.quantity_available}"

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'name': self.name,
            'price': self.price,
            'quantity_available': self.quantity_available
        }

# -------------------- Physical product subclass --------------------

class PhysicalProduct(Product):
    def __init__(self, product_id, name, price, quantity_available, weight):
        super().__init__(product_id, name, price, quantity_available)
        self._weight = weight

    @property
    def weight(self): return self._weight

    def display_details(self):
        return f"{self.product_id} | {self.name} | ₹{self.price:.2f} | Stock: {self.quantity_available} | Weight: {self.weight} kg"

    def to_dict(self):
        data = super().to_dict()
        data.update({'weight': self.weight})
        return data

# -------------------- Digital product subclass --------------------

class DigitalProduct(Product):
    def __init__(self, product_id, name, price, quantity_available, download_link):
        super().__init__(product_id, name, price, quantity_available)
        self._download_link = download_link

    @property
    def download_link(self): return self._download_link

    def display_details(self):
        return f"{self.product_id} | {self.name} | ₹{self.price:.2f} | Download: {self.download_link}"

    def to_dict(self):
        data = super().to_dict()
        data.update({'download_link': self.download_link})
        return data

# -------------------- Cart item class --------------------

class CartItem:
    def __init__(self, product, quantity):
        self._product = product
        self._quantity = quantity

    @property
    def product(self): return self._product
    @property
    def quantity(self): return self._quantity

    @quantity.setter
    def quantity(self, value):
        if value < 0:
            raise ValueError("Quantity cannot be negative.")
        self._quantity = value

    def calculate_subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"Item: {self.product.name}, Quantity: {self.quantity}, Price: ₹{self.product.price:.2f}, Subtotal: ₹{self.calculate_subtotal():.2f}"

    def to_dict(self):
        return {'product_id': self.product.product_id, 'quantity': self.quantity}

#  -------------------- Shopping cart main class --------------------

class ShoppingCart:
    def __init__(self, product_catalog_file='products.json', cart_state_file='cart.json'):
        self._cart_items = {}
        self._product_catalog_file = product_catalog_file
        self._cart_state_file = cart_state_file
        self.catalog = self._load_catalog()
        self._load_cart_state()

    # Load product catalog from JSON
    def _load_catalog(self):
        try:
            with open(self._product_catalog_file, 'r') as f:
                data = json.load(f)
                catalog = {}
                for item in data:
                    try:
                        if 'weight' in item:
                            product = PhysicalProduct(
                                item['product_id'], item['name'],
                                item['price'], item['quantity_available'],
                                item['weight']
                            )
                        elif 'download_link' in item:
                            product = DigitalProduct(
                                item['product_id'], item['name'],
                                item['price'], item['quantity_available'],
                                item['download_link']
                            )
                        else:
                            product = Product(
                                item['product_id'], item['name'],
                                item['price'], item['quantity_available']
                            )
                        catalog[product.product_id] = product
                    except KeyError as e:
                        print(f"Missing key in product data: {e}")
                return catalog
        except FileNotFoundError:
            print(f"Catalog file '{self._product_catalog_file}' not found.")
            return {}

    # Save catalog back to file
    def _save_catalog(self):
        with open(self._product_catalog_file, 'w') as f:
            json.dump([p.to_dict() for p in self.catalog.values()], f)

    # Load cart state from file
    def _load_cart_state(self):
        try:
            with open(self._cart_state_file, 'r') as f:
                data = json.load(f)
                for item in data:
                    pid = item['product_id']
                    if pid in self.catalog:
                        self._cart_items[pid] = CartItem(self.catalog[pid], item['quantity'])
        except FileNotFoundError:
            pass

    # Save current cart state
    def _save_cart_state(self):
        with open(self._cart_state_file, 'w') as f:
            json.dump([p.to_dict() for p in self._cart_items.values()], f)

    # Display all available products
    def display_products(self):
        if not self.catalog:
            print("No products found.")
            return
        print("\n--- Available Products ---")
        for product in self.catalog.values():
            print(product.display_details())

    # Add an item to the cart
    def add_item(self, product_id, quantity):
        product = self.catalog.get(product_id)
        if not product or quantity <= 0 or product.quantity_available < quantity:
            return False
        if product_id in self._cart_items:
            self._cart_items[product_id].quantity += quantity
        else:
            self._cart_items[product_id] = CartItem(product, quantity)
        product.decrease_quantity(quantity)
        self._save_cart_state()
        return True

    # Update quantity (reduce only)
    def update_quantity(self, product_id, quantity_to_remove):
        if product_id not in self._cart_items:
            return False
        cart_item = self._cart_items[product_id]
        current_qty = cart_item.quantity
        if quantity_to_remove > current_qty or quantity_to_remove < 0:
            return False
        new_quantity = current_qty - quantity_to_remove
        cart_item.quantity = new_quantity
        cart_item.product.increase_quantity(quantity_to_remove)
        if new_quantity == 0:
            self._cart_items.pop(product_id)
        self._save_cart_state()
        return True

    # Remove an item from the cart
    def remove_item(self, product_id):
        if product_id in self._cart_items:
            item = self._cart_items.pop(product_id)
            item.product.increase_quantity(item.quantity)
            self._save_cart_state()
            print(f"Removed: {item.product.name}")
            return True
        print("Item not found in cart.")
        return False

    # Calculate total bill
    def get_total(self):
        return sum(item.calculate_subtotal() for item in self._cart_items.values())

    # Display all cart contents
    def display_cart(self):
        if not self._cart_items:
            print("Cart is empty.")
            return
        for item in self._cart_items.values():
            print(item)
        print(f"Total: ₹{self.get_total():.2f}")

    # Print bill and save stock state
    def generate_bill(self):
        print("\n--- BILL RECEIPT ---")
        for item in self._cart_items.values():
            print(item)
        print(f"Grand Total: ₹{self.get_total():.2f}")
        print("Thank you for shopping with us!")
        self._save_catalog()

# -------------------- Run the program interaction --------------------

if os.path.exists('cart.json'):    
    os.remove('cart.json')
cart = ShoppingCart()

while True:
    print("\n--- Online Shopping Cart ---")
    print("1. View All Products")
    print("2. Add Item to Cart")
    print("3. View Cart")
    print("4. Update Quantity")
    print("5. Remove Item")
    print("6. Checkout")
    print("7. Exit")
    choice = input("Choose an option: ")

    if choice == '1':
        cart.display_products()
    elif choice == '2':
        pid = input("Enter product ID: ").strip().upper()
        if pid not in cart.catalog:
            print("Invalid product ID.")
            continue
        try:
            qty = int(input("Enter quantity: "))
            if cart.add_item(pid, qty):
                print("Item added to cart.")
            else:
               print("Failed to add item.")
        except ValueError:
            print("Please enter a valid number.")

    elif choice == '3':
        cart.display_cart()
    elif choice == '4':
        pid = input("Enter product ID to update: ").strip().upper()
        matching_ids = [real_id for real_id in cart._cart_items if real_id == pid]
        if not matching_ids:
            print("Product not in cart.")
        else:
            pid = matching_ids[0]
            print(f"Quantity of '{cart._cart_items[pid].product.name}' in cart: {cart._cart_items[pid].quantity}")
            try:
                rem = int(input("Enter quantity to remove: "))
                if cart.update_quantity(pid, rem):
                    print("Cart updated.")
                else:
                    print("Failed to update cart.")
            except ValueError:
                print("Invalid input.")

    elif choice == '5':
        pid = input("Enter product ID to remove: ").strip().upper()
        matching_ids = [real_id for real_id in cart._cart_items if real_id== pid]
        if not matching_ids:
            print("Item not found in cart.")
        else:
            pid = matching_ids[0]
            cart.remove_item(pid)

    elif choice == '6':
        cart.generate_bill()
        break
    elif choice == '7':
        print("Thank you for visiting...Goodbye!")
        break
    else:
        print("Invalid choice.")
