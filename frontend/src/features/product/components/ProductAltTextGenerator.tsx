
import React, { useEffect, useState } from 'react';
import { fetchProducts } from '../../../api/productApi';
import { shopApi } from '../../../api/shopApi';
import './ProductAltTextGenerator.css';

interface Product {
  id: string;
  name: string;
  imageUrl?: string;
}

const ProductAltTextGenerator: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [altText, setAltText] = useState<string>('');
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const getProducts = async () => {
      try {
        const data = await fetchProducts();
        setProducts(data);
      } catch (err) {
        setError('Failed to fetch products');
      }
    };
    getProducts();
  }, []);

  const handleProductChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedProductId(e.target.value);
    setAltText('');
    setError(null);
  };

  const handleGenerateAltText = async () => {
    setLoading(true);
    setError(null);
    setAltText('');
    setIsEditing(false);
    setCopied(false);
    try {
      const product = products.find(p => p.id === selectedProductId);
      if (!product || !product.imageUrl) {
        setError('Product or image not found');
        setLoading(false);
        return;
      }
      // Call backend to generate alt text from image
      const response = await shopApi.generateFromImage({ imageUrl: product.imageUrl });
      setAltText(response?.descriptions?.[0] || 'No alt text generated');
    } catch (err) {
      setError('Failed to generate alt text');
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = () => {
    setIsEditing(true);
    setCopied(false);
  };

  const handleSaveEdit = () => {
    setIsEditing(false);
  };

  const handleAltTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setAltText(e.target.value);
    setCopied(false);
  };

  const handleCopy = () => {
    if (altText) {
      navigator.clipboard.writeText(altText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <div className="alt-text-generator">
      <h2>Product Alt Text Generator</h2>
      <div className="alt-text-form">
        <label htmlFor="product-select">Select Product:</label>
        <select
          id="product-select"
          value={selectedProductId}
          onChange={handleProductChange}
        >
          <option value="">-- Choose a product --</option>
          {products.map(product => (
            <option key={product.id} value={product.id}>
              {product.name}
            </option>
          ))}
        </select>
        <button
          onClick={handleGenerateAltText}
          disabled={!selectedProductId || loading}
          className="generate-btn"
        >
          {loading ? 'Generating...' : 'Generate Alt Text'}
        </button>
      </div>
      {error && <div className="alt-text-error">{error}</div>}
      {altText && (
        <div className="alt-text-result">
          <strong>Generated Alt Text:</strong>
          {isEditing ? (
            <>
              <textarea
                value={altText}
                onChange={handleAltTextChange}
                rows={3}
                className="alt-text-edit-area"
                placeholder="Edit alt text..."
                title="Edit alt text"
              />
              <button className="generate-btn" onClick={handleSaveEdit}>Save</button>
            </>
          ) : (
            <>
              <p>{altText}</p>
              <div className="alt-text-action-row">
                <button className="generate-btn" onClick={handleEditClick}>Edit</button>
                <button className="generate-btn" onClick={handleCopy}>{copied ? 'Copied!' : 'Copy'}</button>
                <button className="generate-btn" onClick={handleGenerateAltText} disabled={loading}>Regenerate</button>
              </div>
            </>
          )}
        </div>
      )}
      {selectedProductId && (
        <div className="alt-text-image-preview">
          <strong>Image Preview:</strong>
          <img
            src={products.find(p => p.id === selectedProductId)?.imageUrl}
            alt={altText || 'Product image'}
            className="alt-text-image"
          />
        </div>
      )}
    </div>
  );
};

export default ProductAltTextGenerator;
