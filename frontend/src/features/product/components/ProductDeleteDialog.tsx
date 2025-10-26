
import React, { useState } from 'react';
import { deleteProduct } from '../../../api/productApi';
import './ProductDeleteDialog.css';

interface ProductDeleteDialogProps {
  productId: string;
  productName: string;
  onClose: () => void;
  onDeleted?: () => void;
}

const ProductDeleteDialog: React.FC<ProductDeleteDialogProps> = ({ productId, productName, onClose, onDeleted }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [reason, setReason] = useState<string>('');
  const [undo, setUndo] = useState<boolean>(false);

  const handleDelete = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await deleteProduct(productId);
      setSuccess('Product deleted successfully');
      if (onDeleted) onDeleted();
      setTimeout(() => setUndo(true), 1200);
    } catch (err) {
      setError('Failed to delete product');
    } finally {
      setLoading(false);
    }
  };

  const handleUndo = () => {
    // Simulate undo (in real app, call backend to restore)
    setUndo(false);
    setSuccess('Product restored (undo)');
    setTimeout(onClose, 1200);
  };

  return (
    <div className="product-delete-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-title">
      <div className="product-delete-dialog-content">
        <h3 id="delete-title">Delete Product</h3>
        <p>Are you sure you want to delete <strong>{productName}</strong>?</p>
        <label htmlFor="delete-reason">Reason for deletion (optional):</label>
        <textarea
          id="delete-reason"
          value={reason}
          onChange={e => setReason(e.target.value)}
          className="product-delete-reason"
          placeholder="Enter reason..."
          rows={2}
        />
        {error && <div className="product-delete-error">{error}</div>}
        {success && <div className="product-delete-success">{success}</div>}
        <div className="product-delete-actions">
          {!undo ? (
            <>
              <button className="product-delete-btn" onClick={handleDelete} disabled={loading}>
                {loading ? 'Deleting...' : 'Delete'}
              </button>
              <button className="product-cancel-btn" onClick={onClose} disabled={loading}>
                Cancel
              </button>
            </>
          ) : (
            <button className="product-undo-btn" onClick={handleUndo}>Undo Delete</button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductDeleteDialog;
