import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, BadgeCheck, Box, ClipboardList, Package, Plus, RefreshCw, Users } from 'lucide-react';
import { api } from './api';

const emptyProduct = { name: '', sku: '', price: '', quantity_in_stock: '' };
const emptyCustomer = { full_name: '', email: '', phone_number: '' };
const emptyOrder = { customer_id: '', product_id: '', quantity: '' };

function money(value) {
  const num = Number(value || 0);
  return `₹${num.toFixed(2)}`;
}

function Card({ title, value, icon: Icon, subtitle }) {
  return (
    <div className="card summary-card">
      <div className="summary-icon"><Icon size={18} /></div>
      <div>
        <div className="summary-title">{title}</div>
        <div className="summary-value">{value}</div>
        {subtitle && <div className="summary-subtitle">{subtitle}</div>}
      </div>
    </div>
  );
}

function Section({ title, icon: Icon, children, action }) {
  return (
    <section className="card section">
      <div className="section-header">
        <div>
          <div className="section-kicker">{title}</div>
        </div>
        <div className="section-action">{action}</div>
      </div>
      <div className="section-title-row">
        <Icon size={18} />
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Message({ type, text, onClose }) {
  if (!text) return null;
  return (
    <div className={`message ${type}`}>
      <span>{type === 'error' ? <AlertCircle size={16} /> : <BadgeCheck size={16} />}</span>
      <p>{text}</p>
      <button onClick={onClose}>×</button>
    </div>
  );
}

function TextInput(props) {
  return <input className="input" {...props} />;
}

function Select(props) {
  return <select className="input" {...props} />;
}

export default function App() {
  const [summary, setSummary] = useState(null);
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [loading, setLoading] = useState(true);

  const [productForm, setProductForm] = useState(emptyProduct);
  const [editingProductId, setEditingProductId] = useState(null);

  const [customerForm, setCustomerForm] = useState(emptyCustomer);

  const [orderForm, setOrderForm] = useState(emptyOrder);
  const [orderItems, setOrderItems] = useState([]);

  const lowStock = useMemo(() => (summary?.low_stock_products || []).filter(p => Number(p.quantity_in_stock) <= 5), [summary]);

  const reload = async () => {
    setLoading(true);
    try {
      const [summaryData, productData, customerData, orderData] = await Promise.all([
        api.getSummary(),
        api.listProducts(),
        api.listCustomers(),
        api.listOrders(),
      ]);
      setSummary(summaryData);
      setProducts(productData);
      setCustomers(customerData);
      setOrders(orderData);
    } catch (error) {
      setMessage({ type: 'error', text: error.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    reload();
  }, []);

  const showSuccess = (text) => setMessage({ type: 'success', text });
  const showError = (text) => setMessage({ type: 'error', text });

  const handleProductSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...productForm,
        price: Number(productForm.price),
        quantity_in_stock: Number(productForm.quantity_in_stock),
      };
      if (editingProductId) {
        await api.updateProduct(editingProductId, payload);
        showSuccess('Product updated successfully.');
      } else {
        await api.createProduct(payload);
        showSuccess('Product created successfully.');
      }
      setProductForm(emptyProduct);
      setEditingProductId(null);
      await reload();
    } catch (error) {
      showError(error.message);
    }
  };

  const handleEditProduct = (product) => {
    setProductForm({
      name: product.name,
      sku: product.sku,
      price: product.price,
      quantity_in_stock: product.quantity_in_stock,
    });
    setEditingProductId(product.id);
  };

  const handleDeleteProduct = async (id) => {
    if (!window.confirm('Delete this product?')) return;
    try {
      await api.deleteProduct(id);
      showSuccess('Product deleted.');
      await reload();
    } catch (error) {
      showError(error.message);
    }
  };

  const handleCustomerSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createCustomer(customerForm);
      setCustomerForm(emptyCustomer);
      showSuccess('Customer created successfully.');
      await reload();
    } catch (error) {
      showError(error.message);
    }
  };

  const handleDeleteCustomer = async (id) => {
    if (!window.confirm('Delete this customer?')) return;
    try {
      await api.deleteCustomer(id);
      showSuccess('Customer deleted.');
      await reload();
    } catch (error) {
      showError(error.message);
    }
  };

  const addOrderItem = () => {
    if (!orderForm.product_id || !orderForm.quantity) {
      showError('Choose a product and quantity first.');
      return;
    }
    const product = products.find((p) => String(p.id) === String(orderForm.product_id));
    if (!product) {
      showError('Selected product was not found.');
      return;
    }
    setOrderItems((current) => [...current, {
      product_id: Number(orderForm.product_id),
      product_name: product.name,
      sku: product.sku,
      quantity: Number(orderForm.quantity),
      price: Number(product.price),
    }]);
    setOrderForm((current) => ({ ...current, product_id: '', quantity: '' }));
  };

  const removeOrderItem = (index) => {
    setOrderItems((current) => current.filter((_, i) => i !== index));
  };

  const totalDraft = orderItems.reduce((sum, item) => sum + item.price * item.quantity, 0);

  const submitOrder = async (e) => {
    e.preventDefault();
    if (!orderForm.customer_id) {
      showError('Select a customer.');
      return;
    }
    if (orderItems.length === 0) {
      showError('Add at least one order item.');
      return;
    }

    const payload = {
      customer_id: Number(orderForm.customer_id),
      items: orderItems.map(({ product_id, quantity }) => ({ product_id, quantity })),
    };

    try {
      await api.createOrder(payload);
      setOrderItems([]);
      setOrderForm(emptyOrder);
      showSuccess('Order created and inventory updated.');
      await reload();
    } catch (error) {
      showError(error.message);
    }
  };

  const handleDeleteOrder = async (id) => {
    if (!window.confirm('Delete this order and restore inventory?')) return;
    try {
      await api.deleteOrder(id);
      showSuccess('Order deleted and inventory restored.');
      await reload();
    } catch (error) {
      showError(error.message);
    }
  };

  const handleViewOrder = async (id) => {
    try {
      const detail = await api.getOrder(id);
      setSelectedOrder(detail);
      showSuccess('Order details loaded.');
    } catch (error) {
      showError(error.message);
    }
  };

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Inventory & Order Management System</p>
          <h1>Track products, customers, and orders in one place.</h1>
          <p className="hero-copy">
            Production-ready full-stack app with FastAPI, React, PostgreSQL, Docker, and Docker Compose.
          </p>
        </div>
        <button className="primary-btn" onClick={reload}>
          <RefreshCw size={16} /> Refresh
        </button>
      </header>

      <Message type={message.type} text={message.text} onClose={() => setMessage({ type: '', text: '' })} />

      <main className="content">
        <section className="summary-grid">
          <Card title="Products" value={summary?.total_products ?? 0} icon={Package} />
          <Card title="Customers" value={summary?.total_customers ?? 0} icon={Users} />
          <Card title="Orders" value={summary?.total_orders ?? 0} icon={ClipboardList} />
          <Card title="Low stock" value={lowStock.length} icon={Box} subtitle="Stock at or below threshold" />
        </section>

        <div className="grid-2">
          <Section title="Products" icon={Package}>
            <form className="form-grid" onSubmit={handleProductSubmit}>
              <TextInput placeholder="Product name" value={productForm.name} onChange={(e) => setProductForm({ ...productForm, name: e.target.value })} required />
              <TextInput placeholder="SKU" value={productForm.sku} onChange={(e) => setProductForm({ ...productForm, sku: e.target.value })} required />
              <TextInput type="number" step="0.01" min="0" placeholder="Price" value={productForm.price} onChange={(e) => setProductForm({ ...productForm, price: e.target.value })} required />
              <TextInput type="number" min="0" placeholder="Quantity" value={productForm.quantity_in_stock} onChange={(e) => setProductForm({ ...productForm, quantity_in_stock: e.target.value })} required />
              <button className="primary-btn full" type="submit">
                <Plus size={16} /> {editingProductId ? 'Update Product' : 'Add Product'}
              </button>
              {editingProductId && (
                <button className="secondary-btn full" type="button" onClick={() => { setEditingProductId(null); setProductForm(emptyProduct); }}>
                  Cancel Edit
                </button>
              )}
            </form>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th><th>SKU</th><th>Price</th><th>Stock</th><th></th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((product) => (
                    <tr key={product.id}>
                      <td>{product.name}</td>
                      <td>{product.sku}</td>
                      <td>{money(product.price)}</td>
                      <td className={Number(product.quantity_in_stock) <= 5 ? 'low' : ''}>{product.quantity_in_stock}</td>
                      <td className="actions">
                        <button className="tiny-btn" onClick={() => handleEditProduct(product)}>Edit</button>
                        <button className="tiny-btn danger" onClick={() => handleDeleteProduct(product.id)}>Delete</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title="Customers" icon={Users}>
            <form className="form-grid" onSubmit={handleCustomerSubmit}>
              <TextInput placeholder="Full name" value={customerForm.full_name} onChange={(e) => setCustomerForm({ ...customerForm, full_name: e.target.value })} required />
              <TextInput type="email" placeholder="Email address" value={customerForm.email} onChange={(e) => setCustomerForm({ ...customerForm, email: e.target.value })} required />
              <TextInput placeholder="Phone number" value={customerForm.phone_number} onChange={(e) => setCustomerForm({ ...customerForm, phone_number: e.target.value })} required />
              <button className="primary-btn full" type="submit"><Plus size={16} /> Add Customer</button>
            </form>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th><th>Email</th><th>Phone</th><th></th>
                  </tr>
                </thead>
                <tbody>
                  {customers.map((customer) => (
                    <tr key={customer.id}>
                      <td>{customer.full_name}</td>
                      <td>{customer.email}</td>
                      <td>{customer.phone_number}</td>
                      <td className="actions">
                        <button className="tiny-btn danger" onClick={() => handleDeleteCustomer(customer.id)}>Delete</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>
        </div>

        <div className="grid-2">
          <Section title="Create Order" icon={ClipboardList}>
            <form className="form-grid" onSubmit={submitOrder}>
              <Select value={orderForm.customer_id} onChange={(e) => setOrderForm({ ...orderForm, customer_id: e.target.value })} required>
                <option value="">Select customer</option>
                {customers.map((customer) => (
                  <option key={customer.id} value={customer.id}>{customer.full_name}</option>
                ))}
              </Select>

              <Select value={orderForm.product_id} onChange={(e) => setOrderForm({ ...orderForm, product_id: e.target.value })}>
                <option value="">Select product</option>
                {products.map((product) => (
                  <option key={product.id} value={product.id}>{product.name} ({product.quantity_in_stock} left)</option>
                ))}
              </Select>

              <TextInput type="number" min="1" placeholder="Quantity" value={orderForm.quantity} onChange={(e) => setOrderForm({ ...orderForm, quantity: e.target.value })} />
              <button className="secondary-btn full" type="button" onClick={addOrderItem}>Add Item</button>

              <div className="draft-panel">
                {orderItems.length === 0 ? (
                  <p className="muted">No items added yet.</p>
                ) : (
                  orderItems.map((item, index) => (
                    <div key={`${item.product_id}-${index}`} className="draft-item">
                      <div>
                        <strong>{item.product_name}</strong>
                        <div className="muted">{item.sku}</div>
                      </div>
                      <div>{item.quantity} × {money(item.price)}</div>
                      <button className="tiny-btn danger" type="button" onClick={() => removeOrderItem(index)}>Remove</button>
                    </div>
                  ))
                )}
              </div>

              <div className="total-row">
                <span>Draft total</span>
                <strong>{money(totalDraft)}</strong>
              </div>

              <button className="primary-btn full" type="submit">Place Order</button>
            </form>
          </Section>

          <Section title="Orders" icon={ClipboardList}>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th><th>Customer</th><th>Total</th><th>Items</th><th></th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.id}>
                      <td>{order.id}</td>
                      <td>{order.customer_name}</td>
                      <td>{money(order.total_amount)}</td>
                      <td>{order.items.length}</td>
                      <td className="actions">
                        <button className="tiny-btn" onClick={() => handleViewOrder(order.id)}>View</button>
                        <button className="tiny-btn danger" onClick={() => handleDeleteOrder(order.id)}>Delete</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {selectedOrder && (
              <div className="order-detail">
                <div className="section-title-row">
                  <h3>Order #{selectedOrder.id}</h3>
                  <button className="tiny-btn" type="button" onClick={() => setSelectedOrder(null)}>Close</button>
                </div>
                <p><strong>Customer:</strong> {selectedOrder.customer_name}</p>
                <p><strong>Total:</strong> {money(selectedOrder.total_amount)}</p>
                <div className="detail-items">
                  {selectedOrder.items.map((item) => (
                    <div key={`${item.product_id}-${item.sku}`} className="detail-item">
                      <div>
                        <strong>{item.product_name}</strong>
                        <div className="muted">{item.sku}</div>
                      </div>
                      <div>{item.quantity} × {money(item.unit_price)} = {money(item.line_total)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <h3 className="subheading">Low stock products</h3>
            <div className="low-stock-list">
              {lowStock.length === 0 ? (
                <p className="muted">No low stock alerts.</p>
              ) : (
                lowStock.map((product) => (
                  <div key={product.id} className="low-stock-item">
                    <strong>{product.name}</strong>
                    <span>{product.quantity_in_stock} left</span>
                  </div>
                ))
              )}
            </div>
          </Section>
        </div>
      </main>

      {loading && <div className="loading">Loading data...</div>}
    </div>
  );
}
