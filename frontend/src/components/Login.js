import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/Login.css';

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    rememberMe: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const togglePassword = () => setShowPassword(!showPassword);

const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    // Payload
    const payload = {
        email: formData.email, 
        password: formData.password
    };  

    try {
        const response = await fetch('http://127.0.0.1:8000/api/auth/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload), 
        });

        const data = await response.json();
        
        if (response.ok) {
            // JIKA SUKSES
            localStorage.setItem('token', data.key);
            setSuccess('Login Berhasil! Mengalihkan...');
            
            // Redirect HANYA jika sukses
            setTimeout(() => navigate('/dashboard'), 1500);
        } else {
            // JIKA GAGAL (Password Salah / Email tidak ada)
            // Menampilkan pesan error dari backend atau pesan default
            const errorMsg = data.non_field_errors 
                             ? data.non_field_errors[0] 
                             : 'Login gagal. Periksa email dan password.';
            setError(errorMsg);
            
            // JANGAN navigate ke dashboard!
        }
    } 
    catch (err) {
        // Error Jaringan (Server mati / Internet putus)
        console.error(err);
        setError('Gagal menghubungi server. Cek koneksi internet.');
    } finally {
        setLoading(false);
    }
};

  return (
    <div className="login-container">
      <div className="login-header">
        <div className="login-logo">
          <i className="fas fa-brain"></i>
        </div>
        <h1>SLA Predictor</h1>
        <p>Sistem Prediksi Pelanggaran SLA</p>
      </div>

      <form className="login-form" onSubmit={handleSubmit}>
        {error && <div className="error-message"><i className="fas fa-exclamation-circle"></i> {error}</div>}
        {success && <div className="success-message"><i className="fas fa-check-circle"></i> {success}</div>}

        <div className="form-group">
          <label htmlFor="email">Email</label> {/* Ubah htmlFor */}
          <div className="input-wrapper">
            <i className="fas fa-user"></i>
            <input
              type="email" 
              id="email"   
              name="email"  
              value={formData.email} 
              onChange={handleInputChange}
              placeholder="Masukkan email Anda"
              required
            />
          </div>
        </div>

        <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper">
                <i className="fas fa-lock"></i>
                <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Masukkan password Anda"
                required
                />
                <i className={`fas fa-eye${showPassword ? '-slash' : ''} password-toggle`} onClick={togglePassword}></i>
            </div>
        </div>

        <button type="submit" className="login-btn" disabled={loading}>
          <i className="fas fa-sign-in-alt"></i>
          <span>{loading ? 'Memproses...' : 'Masuk ke Sistem'}</span>
        </button>
      </form>

      <div className="divider">
        <span>Demo Account</span>
      </div>

      <div className="demo-login">
        <h4>Akun Demo untuk Testing</h4>
        <div className="demo-credentials">
          <span><strong>Email:</strong> admin@company.com</span>
          <span><strong>Password:</strong> admin123</span>
        </div>
      </div>
    </div>
  );
};

export default Login;