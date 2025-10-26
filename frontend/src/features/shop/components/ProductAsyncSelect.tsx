import React, { useState, useEffect } from 'react';
import { TextField, Spinner, Listbox, Card } from '@shopify/polaris';
import { useRef as reactUseRef } from 'react';

interface Product {
  id: string;
  title: string;
}

interface ProductAsyncSelectProps {
  onSelect: (product: Product) => void;
  selectedProductId?: string;
}

const ProductAsyncSelect: React.FC<ProductAsyncSelectProps> = ({ onSelect, selectedProductId }) => {
  const [search, setSearch] = useState('');
  const [options, setOptions] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [noResults, setNoResults] = useState(false);
  const [highlighted, setHighlighted] = useState<number>(-1);


  // Debounce search
  useEffect(() => {
    const handler = setTimeout(() => {
      if (search.length < 2) {
        setOptions([]);
        setNoResults(false);
        return;
      }
      setLoading(true);
      fetch(`/api/products?search=${encodeURIComponent(search)}`)
        .then(res => res.json())
        .then(data => {
          setOptions(data);
          setNoResults(data.length === 0);
        })
        .catch(() => {
          setOptions([]);
          setNoResults(true);
        })
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(handler);
  }, [search]);

  const handleSelect = (product: Product) => {
    onSelect(product);
    setSearch(product.title);
    setOptions([]);
    setNoResults(false);
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!options.length) return;
    if (e.key === 'ArrowDown') {
      setHighlighted((prev) => (prev + 1) % options.length);
      e.preventDefault();
    } else if (e.key === 'ArrowUp') {
      setHighlighted((prev) => (prev - 1 + options.length) % options.length);
      e.preventDefault();
    } else if (e.key === 'Enter' && highlighted >= 0) {
      handleSelect(options[highlighted]);
      e.preventDefault();
    }
  };

  return (
    <Card>
      <TextField
        label="Search Product"
        value={search}
        onChange={setSearch}
        autoComplete="off"
        placeholder="Type at least 2 characters..."
      />
      {loading && <Spinner size="small" />}
      {!loading && options.length > 0 && (
        <div tabIndex={0} onKeyDown={handleKeyDown}>
          <Listbox
            accessibilityLabel="Product results"
            onSelect={(value) => {
              const product = options.find((o) => o.id === value);
              if (product) handleSelect(product);
            }}
          >
            {options.map((option, idx) => (
              <Listbox.Option
                key={option.id}
                value={option.id}
                selected={option.id === selectedProductId || idx === highlighted}
              >
                {option.title}
              </Listbox.Option>
            ))}
          </Listbox>
        </div>
      )}
      {!loading && noResults && (
        <div className="product-async-select-no-results">No products found.</div>
      )}
    </Card>
  );
};

export default ProductAsyncSelect;

// Properly implement useRef by re-exporting React's useRef
export const useRef = reactUseRef;

