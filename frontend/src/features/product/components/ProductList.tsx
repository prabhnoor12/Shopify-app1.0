
import React, { useEffect, useState } from 'react';
import { fetchProducts } from '../../../api/productApi';
import './ProductList.css';

interface Product {
  id: string;
  name: string;
  description?: string;
  imageUrl?: string;
  price?: number;
}


const PAGE_SIZE = 8;

const ProductList: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);

  useEffect(() => {
    const getProducts = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchProducts();
        setProducts(data);
      } catch (err: any) {
        setError('Failed to fetch products');
      } finally {
        setLoading(false);
      }
    };
    getProducts();
  }, []);

  // Filtering
  const filteredProducts = Array.isArray(products)
    ? products.filter(product =>
        product.name.toLowerCase().includes(filter.toLowerCase()) ||
        (product.description && product.description.toLowerCase().includes(filter.toLowerCase()))
      )
    : [];

  // Pagination
  const totalPages = Math.ceil(filteredProducts.length / PAGE_SIZE);
  const paginatedProducts = Array.isArray(filteredProducts)
    ? filteredProducts.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
    : [];

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilter(e.target.value);
    setCurrentPage(1);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  if (loading) return <div className="product-list-loading">Loading products...</div>;
  if (error) return <div className="product-list-error">{error}</div>;

  return (
    <div className="product-list">
      <div className="product-list-header">
        <h2>Products</h2>
        <input
          type="text"
          placeholder="Filter by name or description..."
          value={filter}
          onChange={handleFilterChange}
          className="product-list-filter"
        />
      </div>
      {!Array.isArray(filteredProducts) || filteredProducts.length === 0 ? (
        <div className="product-list-empty">No products found.</div>
      ) : (
        <ul className="product-list-grid">
          {Array.isArray(paginatedProducts) && paginatedProducts.map(product => (
            <li key={product.id} className="product-list-item">
              <div className="product-card">
                {product.imageUrl ? (
                  <img src={product.imageUrl} alt={product.name} className="product-image" />
                ) : (
                  <div className="product-image-placeholder">No Image</div>
                )}
                <div className="product-info">
                  <h3 className="product-name">{product.name}</h3>
                  {product.description && <p className="product-description">{product.description}</p>}
                  {product.price !== undefined && <p className="product-price">${product.price}</p>}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
      {totalPages > 1 && (
        <div className="product-list-pagination">
          {Array.isArray(Array.from({ length: totalPages }, (_, i) => i + 1)) &&
            Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button
                key={page}
                className={`product-list-page-btn${page === currentPage ? ' active' : ''}`}
                onClick={() => handlePageChange(page)}
                disabled={page === currentPage}
              >
                {page}
              </button>
            ))}
        </div>
      )}
    </div>
  );
};

export default ProductList;
