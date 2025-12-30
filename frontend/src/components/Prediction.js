import { useEffect, useState } from 'react';
import Select from 'react-select'; // 1. Import react-select

const Prediction = () => {
  const [formData, setFormData] = useState({
    priority: '',
    category: '',
    item: '',
    open_date: '',
    due_date: '',
  });
  const [uniqueOptions, setUniqueOptions] = useState({ categories: [], items: [], sub_categories: [] });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingUnique, setLoadingUnique] = useState(true);

  // Fallback options
  const fallbackOptions = {
    categories: [
      { value: 'kegagalan proses', label: 'Kegagalan Proses' },
      { value: 'email', label: 'Email' },
      { value: 're-install', label: 'Re-Install' },
    ],
    items: [
      { value: 'application 332', label: 'Application 332' },
    ],
    sub_categories: [],
  };

  // 2. Custom Styles untuk react-select agar senada dengan form lain
  const customStyles = {
    control: (provided) => ({
      ...provided,
      border: '1px solid #ccc',
      borderRadius: '4px',
      padding: '2px',
      boxShadow: 'none',
      '&:hover': { border: '1px solid #888' }
    }),
    menu: (provided) => ({
      ...provided,
      zIndex: 9999 // Pastikan dropdown muncul di atas elemen lain
    })
  };

  // Fetch unique
  useEffect(() => {
    console.log('Fetching unique...');
    setLoadingUnique(true);
    fetch('http://localhost:8000/api/unique-values/')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (data && data.categories && data.items) {
          setUniqueOptions(data);
        } else {
          setUniqueOptions(fallbackOptions);
        }
        setLoadingUnique(false);
      })
      .catch(err => {
        console.error('Unique error:', err);
        setUniqueOptions(fallbackOptions);
        setLoadingUnique(false);
      });
  }, []);

  // Handle untuk Input Biasa (Priority, Date)
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // 3. Handle Khusus untuk React-Select
  const handleReactSelectChange = (selectedOption, actionMeta) => {
    // actionMeta.name adalah nama field (category/item)
    // selectedOption adalah object { value: '...', label: '...' } atau null jika di-clear
    const value = selectedOption ? selectedOption.value : '';
    setFormData(prev => ({ ...prev, [actionMeta.name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.priority || !formData.category || !formData.item || !formData.open_date || !formData.due_date) {
      alert('Lengkapi semua field wajib!');
      return;
    }

    const openDate = new Date(formData.open_date);
    const dueDate = new Date(formData.due_date);

    if (dueDate < openDate) {
        alert('Validasi Gagal: "Due Date" tidak boleh lebih awal dari "Open Date".');
        return;
    }

    const MAX_SLA_DAYS = 30;
    const diffInMs = dueDate.getTime() - openDate.getTime();
    const diffInDays = diffInMs / (1000 * 60 * 60 * 24);

    if (diffInDays > MAX_SLA_DAYS) {
        alert(`Validasi Gagal: "Due Date" maksimal ${MAX_SLA_DAYS} hari setelah "Open Date".`);
        return;
    }

    setLoading(true);
    setResult(null);
    try {
      const response = await fetch('http://localhost:8000/api/predict/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (response.ok) {
        const data = await response.json();
        setResult(data);
      } else {
        const errorText = await response.text();
        alert('Prediksi gagal: ' + errorText);
      }
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loadingUnique) {
    return (
      <section id="prediction" className="content-section active">
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <h3>Loading form...</h3>
        </div>
      </section>
    );
  }

  return (
    <section id="prediction" className="content-section active">
      <h3>Prediksi SLA untuk Tiket Baru</h3>
      <form onSubmit={handleSubmit} method="post">
        
        {/* Priority tetap pakai Select biasa karena pilihannya sedikit */}
        <div className="form-group">
          <label>Priority:</label>
          <select name="priority" value={formData.priority} onChange={handleInputChange} required>
            <option value="">Pilih Priority</option>
            <option value="4 - Low">Low</option>
            <option value="3 - Medium">Medium</option>
            <option value="2 - High">High</option>
            <option value="1 - Critical">Critical</option>
          </select>
        </div>

        {/* --- CATEGORY MENGGUNAKAN REACT-SELECT --- */}
        <div className="form-group">
          <label>Category:</label>
          <Select
            name="category"
            options={uniqueOptions.categories}
            // Cari object opsi yang value-nya sama dengan state formData.category
            value={uniqueOptions.categories.find(opt => opt.value === formData.category) || null}
            onChange={handleReactSelectChange}
            placeholder="Cari atau Pilih Category..."
            isClearable
            isSearchable
            styles={customStyles}
            required // Note: required html5 tidak jalan sempurna di div react-select, validasi manual di handleSubmit sudah cukup
          />
        </div>

        {/* --- ITEM MENGGUNAKAN REACT-SELECT --- */}
        <div className="form-group">
          <label>Item:</label>
          <Select
            name="item"
            options={uniqueOptions.items}
            // Cari object opsi yang value-nya sama dengan state formData.item
            value={uniqueOptions.items.find(opt => opt.value === formData.item) || null}
            onChange={handleReactSelectChange}
            placeholder="Cari atau Pilih Item..."
            isClearable
            isSearchable
            styles={customStyles}
          />
        </div>

        <div className="form-group">
          <label>Open Date:</label>
          <input type="datetime-local" name="open_date" value={formData.open_date} onChange={handleInputChange} required />
        </div>

        <div className="form-group">
          <label>Due Date:</label>
          <input type="datetime-local" name="due_date" value={formData.due_date} onChange={handleInputChange} required />
        </div>

        <button type="submit" className="btn" disabled={loading}>
          {loading ? 'Memprediksi...' : 'Prediksi SLA'}
        </button>
      </form>

      {result && result.sla_violated !== undefined && (
      <div key={`result-${result.confidence}`} className={`prediction-result ${result.sla_violated ? 'prediction-violation' : 'prediction-safe'}`}>
        <h3>{result.violation_text} Melanggar SLA</h3>
        <p>Confidence: {result.confidence}%</p>
        <p>Days to Due: {result.days_to_due} hari</p>
        <p>Open Hour: {result.open_hour}</p>
        
        <div style={{ marginTop: '15px', fontSize: '0.9rem' }}>
          <h4>Risk Factors:</h4>
          <ul>{result.risk_factors?.map((factor, idx) => <li key={idx}>{factor}</li>) || 'N/A'}</ul>
          
          <h4>Rekomendasi:</h4>
          <p>{result.recommended_actions}</p>
        </div>
      </div>
    )}
    </section>
  );
};

export default Prediction;