from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File
import json
from sqlalchemy.orm import Session
import database

app = FastAPI()

# CREATE operation
@app.post("/products/", response_model=dict)
def create_product(name: str, price_eur: float, description: str = "", link: str = "",
                   db: Session = Depends(database.get_db)):
    db_product = database.Product(name=name, price_eur=price_eur, description=description, link=link)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return {"message": "Product created successfully", "product": db_product}


# READ operation (fetch by ID or name, with pagination)
@app.get("/products/")
def read_products(id: int = Query(None), name: str = Query(None), offset: int = 0, limit: int = 10,
                  db: Session = Depends(database.get_db)):
    # If ID or name is provided, fetch specific product
    if id:
        product = db.query(database.Product).filter(database.Product.id == id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"products": [product]}
    elif name:
        product = db.query(database.Product).filter(database.Product.name == name).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"products": [product]}

    # If no ID or name is provided, apply pagination to retrieve products
    products = db.query(database.Product).offset(offset).limit(limit).all()
    return {
        "offset": offset,
        "limit": limit,
        "total": db.query(database.Product).count(),
        "products": products
    }


# UPDATE operation (update by ID or name)
@app.put("/products/")
def update_product(id: int = Query(None), name: str = Query(None), price_eur: float = None,
                   description: str = None, link: str = None, db: Session = Depends(database.get_db)):
    if id:
        product = db.query(database.Product).filter(database.Product.id == id).first()
    elif name:
        product = db.query(database.Product).filter(database.Product.name == name).first()
    else:
        raise HTTPException(status_code=400, detail="ID or name required for update")

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if price_eur is not None:
        product.price_eur = price_eur
    if description is not None:
        product.description = description
    if link is not None:
        product.link = link

    db.commit()
    db.refresh(product)
    return {"message": "Product updated successfully", "product": product}


# DELETE operation (delete by ID or name)
@app.delete("/products/")
def delete_product(id: int = Query(None), name: str = Query(None), db: Session = Depends(database.get_db)):
    if id:
        product = db.query(database.Product).filter(database.Product.id == id).first()
    elif name:
        product = db.query(database.Product).filter(database.Product.name == name).first()
    else:
        raise HTTPException(status_code=400, detail="ID or name required for delete")

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

# File upload endpoint
@app.post("/upload-json/")
async def upload_json_file(file: UploadFile = File(...)):
    if file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="Invalid file type. Only JSON files are accepted.")

    # Read the JSON content
    contents = await file.read()

    try:
        # Parse the JSON content to ensure it's valid
        json_data = json.loads(contents)
        return {"filename": file.filename, "json_content": json_data}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file.")
