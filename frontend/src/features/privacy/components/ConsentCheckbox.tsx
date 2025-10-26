import React from 'react';
import { Checkbox, Text } from '@shopify/polaris';

interface ConsentCheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
}

const ConsentCheckbox: React.FC<ConsentCheckboxProps> = ({
  checked,
  onChange,
  label = "I consent to the processing of my personal data as described in the Privacy Policy."
}) => {
  return (
    <div>
      <Checkbox
        label={
          <Text as="span">
            {label} <a href="/privacy-policy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
          </Text>
        }
        checked={checked}
        onChange={onChange}
      />
    </div>
  );
};

export default ConsentCheckbox;
