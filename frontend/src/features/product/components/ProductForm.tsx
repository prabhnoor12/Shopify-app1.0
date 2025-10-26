
import React, { useState, useEffect } from 'react';
import { createProduct, updateProduct, fetchProductById } from '../../../api/productApi';
import './ProductForm.css';

interface ProductFormProps {
  productId?: string; // If provided, form is for updating
  onSuccess?: () => void; // Callback after successful create/update
}

interface Product {
  id?: string;
  name: string;
  description?: string;
  imageUrl?: string;
  price?: number;
}

const initialState: Product = {
  name: '',
  description: '',
  imageUrl: '',
  price: undefined,
};

const ProductForm: React.FC<ProductFormProps> = ({ productId, onSuccess }) => {
  const [form, setForm] = useState<Product>(initialState);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState<boolean>(false);

  useEffect(() => {
    if (productId) {
      setLoading(true);
      fetchProductById(productId)
        .then((data) => {
          setForm({
            name: data.name || '',
            description: data.description || '',
            imageUrl: data.imageUrl || '',
            price: data.price,
            id: data.id,
          });
        })
        .catch(() => setError('Failed to load product'))
        .finally(() => setLoading(false));
    }
  }, [productId]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: name === 'price' ? Number(value) : value }));
    setError(null);
    setSuccess(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      if (!form.name) {
        setError('Product name is required');
        setLoading(false);
        return;
      }
      if (form.price !== undefined && form.price < 0) {
        setError('Price cannot be negative');
        setLoading(false);
        return;
      }
      if (form.imageUrl && !/^https?:\/\/.+\.(jpg|jpeg|png|webp|gif)$/i.test(form.imageUrl)) {
        setError('Image URL must be a valid image link');
        setLoading(false);
        return;
      }
      if (productId) {
        await updateProduct(productId, form);
        setSuccess('Product updated successfully');
      } else {
        await createProduct(form);
        setSuccess('Product created successfully');
        setForm(initialState);
        setShowPreview(false);
      }
      if (onSuccess) onSuccess();
    } catch (err) {
      setError('Failed to save product');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setForm(initialState);
    setError(null);
    setSuccess(null);
    setShowPreview(false);
  };

  const handlePreview = (e: React.MouseEvent) => {
    e.preventDefault();
    setShowPreview(true);
  };

  return (
    <form className="product-form" onSubmit={handleSubmit}>
      <h2>{productId ? 'Update Product' : 'Create New Product'}</h2>
      {error && <div className="product-form-error">{error}</div>}
      {success && <div className="product-form-success">{success}</div>}
      <label>
        Name<span className="product-form-required">*</span>:
        <input
          type="text"
          name="name"
          value={form.name}
          onChange={handleChange}
          required
          className="product-form-input"
        />
      </label>
      <label>
        Description:
        <textarea
          name="description"
          value={form.description}
          onChange={handleChange}
          className="product-form-textarea"
        />
      </label>
      <label>
        Image URL:
        <input
          type="url"
          name="imageUrl"
          value={form.imageUrl}
          onChange={handleChange}
          className="product-form-input"
        />
  <button className="product-form-btn product-form-preview-btn" onClick={handlePreview} disabled={!form.imageUrl}>
          Preview Image
        </button>
      </label>
      {showPreview && form.imageUrl && (
        <div className="product-form-image-preview">
          <img src={form.imageUrl} alt="Product preview" className="product-form-image" />
        </div>
      )}
      <label>
        Price:
        <input
          type="number"
          name="price"
          value={form.price === undefined ? '' : form.price}
          onChange={handleChange}
          className="product-form-input"
          min="0"
          step="0.01"
        />
      </label>
      <div className="product-form-actions">
        <button type="submit" className="product-form-btn" disabled={loading}>
          {loading ? 'Saving...' : productId ? 'Update Product' : 'Create Product'}
        </button>
        <button type="button" className="product-form-btn product-form-reset-btn" onClick={handleReset} disabled={loading}>
          Reset
        </button>
      </div>
    </form>
  );
};

export default ProductForm;
