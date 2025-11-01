import React, { useState, useEffect } from 'react';
import { FaChartBar, FaTachometerAlt, FaBoxOpen, FaSearch, FaFlask, FaUsers, FaBolt, FaStore, FaUser } from 'react-icons/fa';
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


  const navigationItems = [
    { path: '/dashboard', label: 'Dashboard', icon: <FaTachometerAlt /> },
    { path: '/analytics', label: 'Analytics', icon: <FaChartBar /> },
    { path: '/products', label: 'Products', icon: <FaBoxOpen /> },
    { path: '/seo', label: 'SEO', icon: <FaSearch /> },
    { path: '/ab-testing', label: 'A/B Testing', icon: <FaFlask /> },
    { path: '/team', label: 'Team', icon: <FaUsers /> },
    { path: '/usage', label: 'Usage', icon: <FaBolt /> },
    { path: '/shop', label: 'Shop', icon: <FaStore /> },
    { path: '/user', label: 'User', icon: <FaUser /> },
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
        <div className="sidebar-header sidebar-gradient">
          <h2>
            <FaStore style={{ marginRight: 8, verticalAlign: 'middle' }} /> Shopify App
          </h2>
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
                  <span className="sidebar-nav-icon">{item.icon}</span>
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
