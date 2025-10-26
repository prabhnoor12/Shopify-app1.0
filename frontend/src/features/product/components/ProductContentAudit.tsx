
import React, { useState, useEffect } from 'react';
import { fetchProducts } from '../../../api/productApi';
import { fetchDescriptionPerformance } from '../../../api/analyticsApi';
import './ProductContentAudit.css';

interface Product {
  id: string;
  name: string;
}


const ProductContentAudit: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([]);
  const [auditResults, setAuditResults] = useState<Record<string, any>>({});
  const [auditHistory, setAuditHistory] = useState<Record<string, any[]>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('');
  const [notification, setNotification] = useState<string>('');

  useEffect(() => {
    fetchProducts()
      .then((data) => setProducts(data))
      .catch(() => setError('Failed to fetch products'));
  }, []);

  // Filter products by name
  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(filter.toLowerCase())
  );

  const handleProductSelect = (id: string) => {
    setSelectedProductIds(prev =>
      prev.includes(id) ? prev.filter(pid => pid !== id) : [...prev, id]
    );
  };

  const handleRunAudit = async () => {
    if (selectedProductIds.length === 0) return;
    setLoading(true);
    setError(null);
    setAuditResults({});
    let newResults: Record<string, any> = {};
    let newHistory = { ...auditHistory };
    try {
      for (const productId of selectedProductIds) {
        const result = await fetchDescriptionPerformance(productId);
        newResults[productId] = result;
        if (!newHistory[productId]) newHistory[productId] = [];
        newHistory[productId].push({ date: new Date().toISOString(), result });
      }
      setAuditResults(newResults);
      setAuditHistory(newHistory);
      setNotification('Audit completed successfully');
    } catch (err) {
      setError('Failed to run content audit');
    } finally {
      setLoading(false);
      setTimeout(() => setNotification(''), 2500);
    }
  };

  // Export results as CSV
  const handleExportCSV = () => {
    if (Object.keys(auditResults).length === 0) return;
    const rows = [
      ['Product', 'Readability', 'SEO Score', 'Keyword Density', 'Suggestions'],
      ...selectedProductIds.map(pid => {
        const r = auditResults[pid] || {};
        return [
          products.find(p => p.id === pid)?.name || pid,
          r.readability || '',
          r.seoScore || '',
          r.keywordDensity || '',
          (r.suggestions || []).join('; ')
        ];
      })
    ];
    const csv = rows.map(row => row.map(String).join(',')).join('\n');
    navigator.clipboard.writeText(csv);
    setNotification('CSV copied to clipboard');
    setTimeout(() => setNotification(''), 2000);
  };

  // Export results as JSON
  const handleExportJSON = () => {
    if (Object.keys(auditResults).length === 0) return;
    navigator.clipboard.writeText(JSON.stringify(auditResults, null, 2));
    setNotification('JSON copied to clipboard');
    setTimeout(() => setNotification(''), 2000);
  };

  // Show only products with poor scores
  const poorProducts = filteredProducts.filter(p => {
    const r = auditResults[p.id];
    return r && (r.seoScore < 50 || r.readability < 50);
  });

  return (
    <div className="product-content-audit">
      <h2>Product Content Audit</h2>
      <div className="audit-form">
        <input
          type="text"
          placeholder="Filter products by name..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="audit-filter"
        />
        <div className="audit-product-list">
          {filteredProducts.map(product => (
            <label key={product.id} className="audit-product-item">
              <input
                type="checkbox"
                checked={selectedProductIds.includes(product.id)}
                onChange={() => handleProductSelect(product.id)}
              />
              {product.name}
            </label>
          ))}
        </div>
        <button
          onClick={handleRunAudit}
          disabled={selectedProductIds.length === 0 || loading}
          className="audit-btn"
        >
          {loading ? 'Running...' : 'Run Audit'}
        </button>
        <button
          onClick={handleExportCSV}
          disabled={Object.keys(auditResults).length === 0}
          className="audit-btn"
        >
          Export CSV
        </button>
        <button
          onClick={handleExportJSON}
          disabled={Object.keys(auditResults).length === 0}
          className="audit-btn"
        >
          Export JSON
        </button>
      </div>
      {notification && <div className="audit-notification">{notification}</div>}
      {error && <div className="audit-error">{error}</div>}
      {Object.keys(auditResults).length > 0 && (
        <div className="audit-result">
          <h3>Audit Results</h3>
          <table className="audit-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Readability</th>
                <th>SEO Score</th>
                <th>Keyword Density</th>
                <th>Suggestions</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {selectedProductIds.map(pid => {
                const r = auditResults[pid] || {};
                return (
                  <tr key={pid} className={r.seoScore < 50 || r.readability < 50 ? 'audit-poor' : ''}>
                    <td>{products.find(p => p.id === pid)?.name || pid}</td>
                    <td>{r.readability ?? '-'}</td>
                    <td>{r.seoScore ?? '-'}</td>
                    <td>{r.keywordDensity ?? '-'}</td>
                    <td>{(r.suggestions || []).map((s: string, i: number) => <div key={i}>{s}</div>)}</td>
                    <td>
                      <button className="audit-btn" onClick={() => alert('Open product edit for ' + pid)}>Apply Fix</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {/* Audit History */}
      {Object.keys(auditHistory).length > 0 && (
        <div className="audit-history">
          <h3>Audit History</h3>
          {selectedProductIds.map(pid => (
            <details key={pid}>
              <summary>{products.find(p => p.id === pid)?.name || pid}</summary>
              <ul>
                {(auditHistory[pid] || []).map((entry, idx) => (
                  <li key={idx}>
                    <strong>{new Date(entry.date).toLocaleString()}:</strong>
                    <pre>{JSON.stringify(entry.result, null, 2)}</pre>
                  </li>
                ))}
              </ul>
            </details>
          ))}
        </div>
      )}
      {/* Poor products filter */}
      {poorProducts.length > 0 && (
        <div className="audit-poor-products">
          <h4>Products needing attention:</h4>
          <ul>
            {poorProducts.map(p => <li key={p.id}>{p.name}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ProductContentAudit;
