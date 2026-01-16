import requests


def get_all_products():
    """
    Retrieves all products from DummyJSON API (returns first 30 by default)
    
    Returns:
        dict: Response containing 'products' list and 'total' count
        Example: {'products': [...], 'total': 100}
    """
    try:
        response = requests.get('https://dummyjson.com/products')
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        # data['products'] contains list of all products
        # data['total'] gives total count
        return data
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching all products: {str(e)}")


def get_product_by_id(product_id):
    """
    Fetches details for a specific product using its unique identifier
    
    Args:
        product_id (int or str): The unique identifier of the product
    
    Returns:
        dict: Single product object
    """
    try:
        response = requests.get(f'https://dummyjson.com/products/{product_id}')
        response.raise_for_status()  # Raise an exception for bad status codes
        product = response.json()
        # Returns single product object
        return product
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching product {product_id}: {str(e)}")


def get_products_with_limit(limit):
    """
    Retrieves a custom number of products, overriding the default limit of 30
    
    Args:
        limit (int): Number of products to retrieve
    
    Returns:
        dict: Response containing 'products' list and 'total' count
    """
    try:
        response = requests.get(f'https://dummyjson.com/products?limit={limit}')
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching products with limit {limit}: {str(e)}")


def search_products(query):
    """
    Searches for products based on a specific query term
    
    Args:
        query (str): Search term (e.g., 'phone', 'laptop')
    
    Returns:
        dict: Response containing 'products' list matching the search query
    """
    try:
        response = requests.get(f'https://dummyjson.com/products/search?q={query}')
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error searching products with query '{query}': {str(e)}")


def create_product_mapping(api_products):
    """
    Creates a mapping of product IDs to product info
    
    Parameters: api_products from fetch_all_products() (or get_all_products())
                Can be either:
                - A list of product dictionaries
                - A dict with 'products' key containing list of products
    
    Returns: dictionary mapping product IDs to info
    Expected Output Format:
    {
        1: {'title': 'iPhone 9', 'category': 'smartphones', 'brand': 'Apple', 'rating': 4.69},
        2: {'title': 'iPhone X', 'category': 'smartphones', 'brand': 'Apple', 'rating': 4.44},
        ...
    }
    """
    # Handle both cases: direct list or dict with 'products' key
    if isinstance(api_products, dict) and 'products' in api_products:
        products_list = api_products['products']
    elif isinstance(api_products, list):
        products_list = api_products
    else:
        raise ValueError("api_products must be a list of products or a dict with 'products' key")
    
    product_mapping = {}
    
    for product in products_list:
        product_id = product.get('id')
        if product_id is not None:
            product_mapping[product_id] = {
                'title': product.get('title', ''),
                'category': product.get('category', ''),
                'brand': product.get('brand', ''),
                'rating': product.get('rating', 0.0)
            }
    
    return product_mapping


def enrich_sales_data(transactions, product_mapping):
    """
    Enriches transaction data with API product information

    Parameters:
    - transactions: list of transaction dictionaries
    - product_mapping: dictionary from create_product_mapping()

    Returns: list of enriched transaction dictionaries

    Expected Output Format (each transaction):
    {
        'TransactionID': 'T001',
        'Date': '2024-12-01',
        'ProductID': 'P101',
        'ProductName': 'Laptop',
        'Quantity': 2,
        'UnitPrice': 45000.0,
        'CustomerID': 'C001',
        'Region': 'North',
        # NEW FIELDS ADDED FROM API:
        'API_Category': 'laptops',
        'API_Brand': 'Apple',
        'API_Rating': 4.7,
        'API_Match': True  # True if enrichment successful, False otherwise
    }

    Enrichment Logic:
    - Extract numeric ID from ProductID (P101 → 101, P5 → 5)
    - If ID exists in product_mapping, add API fields
    - If ID doesn't exist, set API_Match to False and other fields to None
    - Handle all errors gracefully

    File Output:
    - Save enriched data to 'data/enriched_sales_data.txt'
    - Use same pipe-delimited format
    - Include new columns in header
    """
    import os
    import re
    
    enriched_transactions = []
    
    for transaction in transactions:
        # Create a copy of the transaction to avoid modifying the original
        enriched_transaction = transaction.copy()
        
        # Extract numeric ID from ProductID (P101 → 101, P5 → 5)
        product_id_str = str(transaction.get('ProductID', ''))
        
        # Try to extract numeric part from ProductID
        numeric_id = None
        try:
            # Match pattern like P101, P5, etc.
            match = re.search(r'P(\d+)', product_id_str, re.IGNORECASE)
            if match:
                numeric_id = int(match.group(1))
        except (ValueError, AttributeError):
            pass
        
        # Look up in product_mapping
        if numeric_id is not None and numeric_id in product_mapping:
            product_info = product_mapping[numeric_id]
            enriched_transaction['API_Category'] = product_info.get('category', '')
            enriched_transaction['API_Brand'] = product_info.get('brand', '')
            enriched_transaction['API_Rating'] = product_info.get('rating', 0.0)
            enriched_transaction['API_Match'] = True
        else:
            # ID doesn't exist in mapping
            enriched_transaction['API_Category'] = None
            enriched_transaction['API_Brand'] = None
            enriched_transaction['API_Rating'] = None
            enriched_transaction['API_Match'] = False
        
        enriched_transactions.append(enriched_transaction)
    
    # Save enriched data to file
    output_file = 'data/enriched_sales_data.txt'
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Write header with new columns
    header = "TransactionID|Date|ProductID|ProductName|Quantity|UnitPrice|CustomerID|Region|API_Category|API_Brand|API_Rating|API_Match\n"
    
    # Write enriched transactions
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(header)
        
        for transaction in enriched_transactions:
            # Format None values as empty strings for file output
            api_category = transaction.get('API_Category') if transaction.get('API_Category') is not None else ''
            api_brand = transaction.get('API_Brand') if transaction.get('API_Brand') is not None else ''
            api_rating = transaction.get('API_Rating') if transaction.get('API_Rating') is not None else ''
            api_match = transaction.get('API_Match', False)
            
            line = (
                f"{transaction.get('TransactionID', '')}|"
                f"{transaction.get('Date', '')}|"
                f"{transaction.get('ProductID', '')}|"
                f"{transaction.get('ProductName', '')}|"
                f"{transaction.get('Quantity', '')}|"
                f"{transaction.get('UnitPrice', '')}|"
                f"{transaction.get('CustomerID', '')}|"
                f"{transaction.get('Region', '')}|"
                f"{api_category}|"
                f"{api_brand}|"
                f"{api_rating}|"
                f"{api_match}\n"
            )
            file.write(line)
    
    return enriched_transactions


def save_enriched_data(enriched_transactions, filename='data/enriched_sales_data.txt'):
    """
    Saves enriched transactions back to file
    
    Args:
        enriched_transactions (list): List of enriched transaction dictionaries
        filename (str): Path to output file (default: 'data/enriched_sales_data.txt')
    
    Expected File Format:
    Header: TransactionID|Date|ProductID|ProductName|Quantity|UnitPrice|CustomerID|Region|API_Category|API_Brand|API_Rating|API_Match
    Example: T001|2024-12-01|P101|Laptop|2|45000.0|C001|North|laptops|Apple|4.7|True
    
    Requirements:
    - Output file with all original fields plus API fields
    - Pipe-delimited format
    - Handle None values appropriately
    """
    import os
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
    
    # Write header with all columns
    header = "TransactionID|Date|ProductID|ProductName|Quantity|UnitPrice|CustomerID|Region|API_Category|API_Brand|API_Rating|API_Match\n"
    
    # Write enriched transactions to file
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(header)
        
        for transaction in enriched_transactions:
            # Format None values as empty strings for file output
            api_category = transaction.get('API_Category') if transaction.get('API_Category') is not None else ''
            api_brand = transaction.get('API_Brand') if transaction.get('API_Brand') is not None else ''
            api_rating = transaction.get('API_Rating') if transaction.get('API_Rating') is not None else ''
            api_match = transaction.get('API_Match', False)
            
            # Handle None values for original fields as well
            transaction_id = transaction.get('TransactionID', '') or ''
            date = transaction.get('Date', '') or ''
            product_id = transaction.get('ProductID', '') or ''
            product_name = transaction.get('ProductName', '') or ''
            quantity = transaction.get('Quantity', '') or ''
            unit_price = transaction.get('UnitPrice', '') or ''
            customer_id = transaction.get('CustomerID', '') or ''
            region = transaction.get('Region', '') or ''
            
            line = (
                f"{transaction_id}|"
                f"{date}|"
                f"{product_id}|"
                f"{product_name}|"
                f"{quantity}|"
                f"{unit_price}|"
                f"{customer_id}|"
                f"{region}|"
                f"{api_category}|"
                f"{api_brand}|"
                f"{api_rating}|"
                f"{api_match}\n"
            )
            file.write(line)
