import React, { useState, useEffect } from 'react';
import { TextField, Spinner, Listbox, Card } from '@shopify/polaris';

interface AsyncCollectionSelectProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  fetchUrl: string;
}

const AsyncCollectionSelect: React.FC<AsyncCollectionSelectProps> = ({ label, value, onChange, fetchUrl }) => {
  const [search, setSearch] = useState('');
  const [options, setOptions] = useState<{id: string, title: string}[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (search.length < 2) {
      setOptions([]);
      return;
    }
    setLoading(true);
    fetch(`${fetchUrl}?search=${encodeURIComponent(search)}`)
      .then(res => res.json())
      .then(data => setOptions(data))
      .catch(() => setOptions([]))
      .finally(() => setLoading(false));
  }, [search, fetchUrl]);

  return (
    <Card>
      <TextField
        label={label}
        value={search || value}
        onChange={(val) => {
          setSearch(val);
          onChange('');
        }}
        autoComplete="off"
        placeholder="Type at least 2 characters..."
      />
      {loading && <Spinner size="small" />}
      {!loading && Array.isArray(options) && options.length > 0 && (
        <Listbox
          accessibilityLabel={`${label} results`}
          onSelect={(selected) => {
            const found = options.find(o => o.id === selected);
            if (found) {
              onChange(found.id);
              setSearch(found.title);
            }
          }}
        >
          {options.map((option) => (
            <Listbox.Option key={option.id} value={option.id} selected={option.id === value}>
              {option.title}
            </Listbox.Option>
          ))}
        </Listbox>
      )}
    </Card>
  );
};

export default AsyncCollectionSelect;
