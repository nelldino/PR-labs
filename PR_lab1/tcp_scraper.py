import socket
import ssl
import datetime
from functools import reduce

import requests  # To make HTTP requests
from bs4 import BeautifulSoup

# Target server and port
host = 'librarius.md'
port = 443  # HTTPS uses port 443
base_url = f"https://{host}"  # Base URL for relative links

# HTTP request template (GET request for a specific page)
request = f"GET /ro/books/page/1 HTTP/1.1\r\nHost: {host}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0.0.0 Safari/537.36\r\nConnection: close\r\n\r\n"

# Create an SSL context
context = ssl.create_default_context()

# Create a socket and connect to the server
with socket.create_connection((host, port)) as sock:
    # Wrap the socket with the SSL context
    with context.wrap_socket(sock, server_hostname=host) as ssl_sock:
        # Send the HTTP request
        ssl_sock.sendall(request.encode())

        # Receive the response data in chunks
        response_data = b""
        while True:
            chunk = ssl_sock.recv(4096)
            if not chunk:
                break
            response_data += chunk

# Decode the response to string
response_text = response_data.decode()

# Find the start of the HTTP body (after headers)
header_end_idx = response_text.find("\r\n\r\n")
if header_end_idx != -1:
    html_body = response_text[header_end_idx + 4:]  # The actual HTML content

# Pass the HTML body to BeautifulSoup for scraping
soup = BeautifulSoup(html_body, features="html.parser")

# Product validation function
def validate_product_data(name, price, description):
    if not name:
        print("Validation failed: Product name is empty.")
        return False

    # Clean the price by removing non-numeric characters
    price_cleaned = price.replace('lei', '').strip()  # Remove 'lei' and any extra spaces

    try:
        price_value = float(price_cleaned)  # Convert cleaned price to float
        if price_value <= 0:
            print(f"Validation failed: Product price '{price}' must be greater than zero.")
            return False
    except ValueError:
        print(f"Validation failed: Product price '{price}' is not a valid number.")
        return False

    return True

# Headers for making requests to individual product pages
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0.0.0 Safari/537.36'
}

product_data = []
productlist = soup.find_all('div', class_='anyproduct-card')

for product in productlist:
    product_name = product.find('div', class_='card-title').text.strip()
    product_price = product.find('div', class_='card-price').text.strip()

    # Extract product link
    product_link_tag = product.find('a', href=True)
    if product_link_tag:
        product_link = product_link_tag['href']
        # If the href is a relative link, append the base URL
        if not product_link.startswith('http'):
            product_link = base_url + product_link

        # Make a request to the product's detail page to get the description
        product_page = requests.get(product_link, headers=headers)
        product_soup = BeautifulSoup(product_page.text, features="html.parser")

        # Safely extract the description from the product page
        descriptions = product_soup.find_all('div', class_='book-page-description')

        # Check for the one without the id
        for desc in descriptions:
            if not desc.has_attr('id'):
                product_description = desc.text.strip()
                break
        else:
            product_description = "No description available"

        # Validate product data before storing
        if validate_product_data(product_name, product_price, product_description):
            book = {
                'product_name': product_name,
                'product_price': product_price,
                'product_description': product_description,
                'product_link': product_link  # Optionally store the link as well
            }
            product_data.append(book)  # Append the product to the list

            # Print the valid product data in the same format
            print("Valid Product:")
            print(f"Product Name: {book['product_name']}")
            print(f"Product Price: {book['product_price']}")
            print(f"Product Description: {book['product_description']}")
            print(f"Product Link: {book['product_link']}")
            print("\n" + "-" * 40 + "\n")  # Print a separator line for better readability
        else:
            print(f"Product data validation failed for {product_name}.")
    else:
        print(f"No link found for product: {product_name}")
def convert_price(price_str):
    # Extract numerical value from price string
    if isinstance(price_str, float):  # If it's already a float, return it
        return price_str
    price_value = float(price_str.replace('lei', '').strip())
    # Convert to EUR
    return price_value * 0.05  # MDL to EUR conversion

# Filter function to check if the product price is within a range
def filter_price_range(product, min_price, max_price):
    price_value = convert_price(product['product_price'])  # Convert to EUR for comparison
    return min_price <= price_value <= max_price

# Price range for filtering (example: 10 EUR to 50 EUR)
min_price = 5
max_price = 50

# Mapping product prices and filtering products
filtered_products = list(
    filter(lambda product: filter_price_range(product, min_price, max_price), product_data)
)

# Convert prices to EUR for filtered products
for product in filtered_products:
    product['product_price'] = convert_price(product['product_price'])

# Use reduce to calculate the sum of the filtered product prices
total_price_eur = reduce(lambda acc, product: acc + product['product_price'], filtered_products, 0)

# Create a new data model with the results
result_data = {
    'filtered_products': filtered_products,
    'total_price': total_price_eur,
    'timestamp': datetime.datetime.utcnow().isoformat()   # UTC timestamp
}

print("Filtered Products:")
for product in result_data['filtered_products']:
    print(f"Product Name: {product['product_name']}")
    print(f"Product Price (EUR): {product['product_price']:.2f}")
    print(f"Product Description: {product['product_description']}")
    print(f"Product Link: {product['product_link']}")
    print("\n" + "-"*40 + "\n")  # Print a separator line for better readability

print(f"Total Price (EUR): {result_data['total_price']:.2f}")
print(f"Timestamp: {result_data['timestamp']}")