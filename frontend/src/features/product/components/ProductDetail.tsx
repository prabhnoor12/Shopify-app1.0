
import React, { useEffect, useState } from 'react';
import { fetchProductById } from '../../../api/productApi';
import './ProductDetail.css';

interface ProductDetailProps {
  productId: string;
}

interface Product {
  id: string;
  name: string;
  description?: string;
  imageUrl?: string;
  price?: number;
}

const ProductDetail: React.FC<ProductDetailProps> = ({ productId }) => {
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchProductById(productId)
      .then(data => setProduct(data))
      .catch(() => setError('Failed to fetch product'))
      .finally(() => setLoading(false));
  }, [productId]);

  if (loading) return <div className="product-detail-loading">Loading...</div>;
  if (error) return <div className="product-detail-error">{error}</div>;
  if (!product) return <div className="product-detail-empty">Product not found.</div>;

  // Actions
  const handleEdit = () => {
    alert('Edit product: ' + product.id);
  };
  const handleDelete = () => {
    alert('Delete product: ' + product.id);
  };
  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href + '?productId=' + product.id);
    alert('Product link copied to clipboard!');
  };

  return (
    <div className="product-detail">
      <div className="product-detail-header">
        {product.imageUrl && (
          <img src={product.imageUrl} alt={product.name} className="product-detail-image" />
        )}
        <div className="product-detail-info">
          <h2 className="product-detail-name">{product.name}</h2>
          {product.description && <p className="product-detail-description">{product.description}</p>}
          {product.price !== undefined && <p className="product-detail-price">Price: ${product.price}</p>}
        </div>
      </div>
      <div className="product-detail-actions">
        <button className="product-detail-btn" onClick={handleEdit}>Edit</button>
        <button className="product-detail-btn" onClick={handleDelete}>Delete</button>
        <button className="product-detail-btn" onClick={handleShare}>Share</button>
      </div>
    </div>
  );
};

export default ProductDetail;
