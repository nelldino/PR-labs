import socket
import ssl
import datetime
from functools import reduce
import requests  # To make HTTP requests
from bs4 import BeautifulSoup

# Target server and port
host = 'librarius.md'
port = 443  # HTTPS uses port 443
base_url = f"https://{host}"

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

response_text = response_data.decode()

# Find the start of the HTTP body (after headers)
header_end_idx = response_text.find("\r\n\r\n")
if header_end_idx != -1:
    html_body = response_text[header_end_idx + 4:]  # The actual HTML content

# Pass the HTML body content to the scraping logic
soup = BeautifulSoup(html_body, features="html.parser")


# Product validation function
def validate_product_data(name, price, description):
    if not name:
        print("Validation failed: Product name is empty.")
        return False

    price_cleaned = price.replace('lei', '').strip()
    try:
        price_value = float(price_cleaned)
        if price_value <= 0:
            print(f"Validation failed: Product price '{price}' must be greater than zero.")
            return False
    except ValueError:
        print(f"Validation failed: Product price '{price}' is not a valid number.")
        return False

    return True


# Convert price from MDL to EUR
def convert_price(price_str):
    if isinstance(price_str, float):
        return price_str
    price_value = float(price_str.replace('lei', '').strip())
    return price_value * 0.05


# Filter products based on price range
def filter_price_range(product, min_price, max_price):
    price_value = convert_price(product['product_price'])
    return min_price <= price_value <= max_price


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

        if not product_link.startswith('http'):
            product_link = base_url + product_link

        # Get the description of a book
        product_page = requests.get(product_link, headers=headers)
        product_soup = BeautifulSoup(product_page.text, features="html.parser")

        descriptions = product_soup.find_all('div', class_='book-page-description')

        # Since the HTML page contains two tags with the same class that differentiate by an id, we extract the one description class without that id
        if not product_link.startswith('http'):
            product_link = base_url + product_link

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
                'product_link': product_link
            }
            product_data.append(book)  # Append the product to the list

            # Print the valid product data in the same format
            print("Valid Product:")
            print(f"Product Name: {book['product_name']}")
            print(f"Product Price: {book['product_price']}")
            print(f"Product Description: {book['product_description']}")
            print(f"Product Link: {book['product_link']}")
            print("\n" + "-" * 40 + "\n")
        else:
            print(f"Product data validation failed for {product_name}.")
    else:
        print(f"No link found for product: {product_name}")

# Filter price range and calculate total
min_price = 5
max_price = 50

filtered_products = list(
    filter(lambda product: filter_price_range(product, min_price, max_price), product_data)
)

for product in filtered_products:
    product['product_price'] = convert_price(product['product_price'])

total_price_eur = reduce(lambda acc, product: acc + product['product_price'], filtered_products, 0)

result_data = {
    'filtered_products': filtered_products,
    'total_price': total_price_eur,
    'timestamp': datetime.datetime.utcnow().isoformat()  # UTC timestamp
}


def escape_json_string(s):
    return s.replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')

def serialize_to_json(data, indent_level=0):
    indent = ' ' * (indent_level * 4)  # 4 spaces per indent level
    if isinstance(data, dict):
        json_items = []
        for key, value in data.items():
            json_key = f'"{escape_json_string(key)}"'
            json_value = serialize_to_json(value, indent_level + 1)
            json_items.append(f'{indent}    {json_key}: {json_value}')
        return '{\n' + ',\n'.join(json_items) + f'\n{indent}}}'

    elif isinstance(data, list):
        json_items = [serialize_to_json(item, indent_level + 1) for item in data]
        return '[\n' + ',\n'.join(json_items) + f'\n{indent}]'

    elif isinstance(data, str):
        return f'"{escape_json_string(data)}"'

    elif isinstance(data, (int, float)):
        return str(data)

    elif data is None:
        return 'null'

    raise ValueError(f"Unsupported data type: {type(data)}")


data_json = serialize_to_json(result_data)
print("Serialized JSON Data:")
print(data_json)


def serialize_to_xml(data, root_tag='root', indent_level=0):
    """ Manually serialize data to XML format with indentation. """
    indent = ' ' * (indent_level * 4)  # 4 spaces per indent level
    xml_items = []

    def serialize_item(key, value, level):
        inner_indent = ' ' * (level * 4)
        if isinstance(value, dict):
            child_items = [
                f'{inner_indent}<{k}>{serialize_item(k, v, level + 1)}</{k}>' for k, v in value.items()
            ]
            return f'\n{inner_indent}' + f'\n'.join(child_items) + f'\n{inner_indent}'
        elif isinstance(value, list):
            item_tags = [
                f'{inner_indent}<{key}_item>{serialize_item(key, item, level + 1)}</{key}_item>'
                for item in value
            ]
            return '\n' + '\n'.join(item_tags) + f'\n{inner_indent}'
        elif isinstance(value, str):
            return f'<![CDATA[{value}]]>'
        else:
            return str(value)

    # Start the XML document with indentation
    xml_items.append(f'{indent}<{root_tag}>')
    for key, value in data.items():
        xml_items.append(f'{indent}    <{key}>{serialize_item(key, value, indent_level + 1)}</{key}>')
    xml_items.append(f'{indent}</{root_tag}>')

    return '\n'.join(xml_items)

data_xml = serialize_to_xml(result_data)
print("Serialized XML Data (Organized):")
print(data_xml)



# Custom Serialization Functions
def custom_serialize(obj, indent_level=0):
    indent = ' ' * (indent_level * 4)  # Indentation level (4 spaces per level)
    if isinstance(obj, str):
        return f"{indent}S[{len(obj)}]{obj}"
    elif isinstance(obj, (int, float)):
        return f"{indent}N{obj}"
    elif isinstance(obj, list):
        serialized_list = '\n'.join([custom_serialize(item, indent_level + 1) for item in obj])
        return f"{indent}L[{len(obj)}]\n{serialized_list}"
    elif isinstance(obj, dict):
        serialized_dict = '\n'.join(
            [f"{indent}{custom_serialize(k, indent_level + 1)}{custom_serialize(v, indent_level + 1)}"
             for k, v in obj.items()]
        )
        return f"{indent}D[{len(obj)}]\n{serialized_dict}"
    else:
        raise ValueError(f"Unsupported data type: {type(obj)}")


# Example use
def serialize_data(data):
    return custom_serialize(data)


def custom_deserialize(data):
    def parse_value(data, idx):
        # Skip any whitespace characters (spaces, newlines, tabs)
        while idx < len(data) and data[idx].isspace():
            idx += 1

        if idx >= len(data):
            raise ValueError("Reached the end of data unexpectedly.")

        type_marker = data[idx]

        if type_marker == 'S':
            length_end_idx = data.index(']', idx)
            length = int(data[idx + 2:length_end_idx])
            start_content = length_end_idx + 1
            return data[start_content:start_content + length], start_content + length

        elif type_marker == 'N':
            number_end_idx = idx + 1
            while number_end_idx < len(data) and (data[number_end_idx].isdigit() or data[number_end_idx] == '.'):
                number_end_idx += 1
            return float(data[idx + 1:number_end_idx]), number_end_idx

        elif type_marker == 'L':
            length_end_idx = data.index(']', idx)
            length = int(data[idx + 2:length_end_idx])
            start_content = length_end_idx + 1
            items = []
            while length > 0:
                item, next_idx = parse_value(data, start_content)
                items.append(item)
                start_content = next_idx
                length -= 1
            return items, start_content

        elif type_marker == 'D':
            length_end_idx = data.index(']', idx)
            length = int(data[idx + 2:length_end_idx])
            start_content = length_end_idx + 1
            items = {}
            while length > 0:
                key, next_idx = parse_value(data, start_content)
                value, next_idx = parse_value(data, next_idx)
                items[key] = value
                start_content = next_idx
                length -= 1
            return items, start_content

        else:
            raise ValueError(f"Unknown type marker '{type_marker}' at index {idx}. Data: {data[idx:idx + 20]}")

    return parse_value(data, 0)[0]


def deserialize_data(serialized_str):
    return custom_deserialize(serialized_str)


serialized = serialize_data(result_data)
print("Serialized Data:")
print(serialized)

deserialized = deserialize_data(serialized)
print("\nDeserialized Data:")
print(deserialized)

data_json= serialize_to_json(result_data)
data_xml= serialize_to_xml(result_data)

url = 'http://localhost:8000/upload'

response_json = requests.post(url, data=data_json, headers={'Content-Type': 'application/json'}, auth=('301', '408'))
print('JSON Response:', response_json.status_code, response_json.text)

response_xml = requests.post(url, data=data_xml, headers={'Content-Type': 'application/xml'}, auth=('301', '408'))
print('XML Response:', response_xml.status_code, response_xml.text)
