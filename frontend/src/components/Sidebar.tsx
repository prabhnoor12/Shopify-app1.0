import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Sidebar.css';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    // Close sidebar on route change in mobile
    if (isMobile && isOpen) {
      onClose();
    }
  }, [location.pathname, isMobile, isOpen, onClose]);

  const navigationItems = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/analytics', label: 'Analytics' },
    { path: '/products', label: 'Products' },
    { path: '/seo', label: 'SEO' },
    { path: '/ab-testing', label: 'A/B Testing' },
    { path: '/team', label: 'Team' },
    { path: '/usage', label: 'Usage' },
    { path: '/shop', label: 'Shop ' },
    { path: '/user', label: 'User' },
    
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <>
      {/* Mobile overlay - only show when sidebar is not full screen */}
      {!isMobile && isOpen && (
        <div className="sidebar-overlay" onClick={onClose} />
      )}

      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''} ${isMobile ? 'sidebar-mobile' : ''}`}>
        <div className="sidebar-header">
          <h2>Shopify App</h2>
          {isMobile && (
            <button className="sidebar-close-btn" onClick={onClose} aria-label="Close sidebar">
              ✕
            </button>
          )}
        </div>

        <nav className="sidebar-nav">
          <ul className="sidebar-nav-list">
            {navigationItems.map((item) => (
              <li key={item.path} className="sidebar-nav-item">
                <button
                  className={`sidebar-nav-link ${
                    location.pathname.startsWith(item.path) ? 'sidebar-nav-link-active' : ''
                  }`}
                  onClick={() => handleNavigation(item.path)}
                  aria-label={`Navigate to ${item.label}`}
                >
                  <span className="sidebar-nav-text">{item.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <div className="sidebar-footer">
          <p>© 2024 Shopify App</p>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
