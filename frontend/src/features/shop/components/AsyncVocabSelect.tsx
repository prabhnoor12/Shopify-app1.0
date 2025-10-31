import React, { useState, useEffect } from 'react';
import { TextField, Spinner, Listbox, Card } from '@shopify/polaris';

interface AsyncVocabSelectProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  onSelect: (item: string) => void;
  fetchUrl: string;
}

const AsyncVocabSelect: React.FC<AsyncVocabSelectProps> = ({ label, value, onChange, onSelect, fetchUrl }) => {
  const [search, setSearch] = useState('');
  const [options, setOptions] = useState<string[]>([]);
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
        value={value}
        onChange={(val) => {
          setSearch(val);
          onChange(val);
        }}
        autoComplete="off"
        placeholder="Type at least 2 characters..."
      />
      {loading && <Spinner size="small" />}
      {!loading && Array.isArray(options) && options.length > 0 && (
        <Listbox
          accessibilityLabel={`${label} results`}
          onSelect={(selected) => onSelect(selected)}
        >
          {options.map((option) => (
            <Listbox.Option key={option} value={option} selected={option === value}>
              {option}
            </Listbox.Option>
          ))}
        </Listbox>
      )}
    </Card>
  );
};

export default AsyncVocabSelect;
