import bs4
import requests

url = 'https://librarius.md'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'}
product_data = []  # List to hold all product information


# Function to validate product data
def validate_product_data(name, price, description):
    if not name:
        print("Validation failed: Product name is empty.")
        return False
    # if not description:
    #     print("Validation failed: Product description is empty.")
    #     return False

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


# Loop through 10 pages of the website
for x in range(1, 10):
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
            # print(
            #     f"Validating product: Name='{product_name}', Price='{product_price}', Description='{product_description}'")
            if validate_product_data(product_name, product_price, product_description):
                book = {
                    'product_name': product_name,
                    'product_price': product_price,
                    'product_description': product_description,
                    'product_link': product_link  # Optionally store the link as well
                }
                product_data.append(book)  # Append the product to the list

                # Print the book data
                print("Valid product:", book)
            else:
                print(f"Product data validation failed for {product_name}.")
        else:
            print(f"No link found for product: {product_name}")
