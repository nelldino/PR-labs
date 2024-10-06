import bs4
import requests
import datetime
from functools import reduce

url = 'https://librarius.md'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'}
product_data = []  # List to hold all product information

# Function to validate product data
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

# Loop through 1 page of the website
for x in range(1, 2):
    r = requests.get(f'https://librarius.md/ro/books/page/{x}', headers=headers)
    soup = bs4.BeautifulSoup(r.text, features="html.parser")

    productlist = soup.find_all('div', class_='anyproduct-card')

    # Loop through each product card
    for product in productlist:
        product_name = product.find('div', class_='card-title').text.strip()
        product_price = product.find('div', class_='card-price').text.strip()

        # Extract product link
        product_link_tag = product.find('a', href=True)

        if product_link_tag:
            product_link = product_link_tag['href']
            # If the href is a relative link, append the base URL
            if not product_link.startswith('http'):
                product_link = url + product_link

            # Make a request to the product's detail page to get the description
            product_page = requests.get(product_link, headers=headers)
            product_soup = bs4.BeautifulSoup(product_page.text, features="html.parser")

            # Safely extract the description from the product page, excluding the one with id="product-supply"
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

    # The rest of your existing code continues here...


# Define a price conversion function
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
    'timestamp': datetime.datetime.utcnow().isoformat()  # UTC timestamp
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
