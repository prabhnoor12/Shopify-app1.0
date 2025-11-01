import React, { useState } from 'react';
import { shopApi } from '../../../api/shopApi';
import './ProductShopifySync.css';

const ProductShopifySync: React.FC = () => {
  const [syncing, setSyncing] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [products, setProducts] = useState<any[]>([]);

  const handleSync = async () => {
    setSyncing(true);
    setError(null);
    setSuccess(null);
    try {
      // Fetch products from Shopify backend
      const shopifyProducts = await shopApi.getProducts();
      setProducts(shopifyProducts);
      setSuccess('Products synced successfully from Shopify!');
    } catch (err: any) {
      setError('Failed to sync products from Shopify.');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="product-shopify-sync">
      <h2>Shopify Product Sync</h2>
      <button onClick={handleSync} disabled={syncing} className="sync-btn">
        {syncing ? 'Syncing...' : 'Sync Products from Shopify'}
      </button>
      {success && <div className="success-msg">{success}</div>}
      {error && <div className="error-msg">{error}</div>}
      <div className="product-list">
        {Array.isArray(products) && products.length > 0 ? (
          <ul>
            {products.map((product) => (
              <li key={product.id}>{product.title}</li>
            ))}
          </ul>
        ) : (
          <p>No products synced yet.</p>
        )}
      </div>
    </div>
  );
};

export default ProductShopifySync;
