import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PieController,
  PointElement,
  ScatterController,
  Title, Tooltip,
} from 'chart.js';
import { useEffect, useMemo, useState } from 'react';
import { Bar, Doughnut, Line, Pie, Scatter } from 'react-chartjs-2';
import { useSearchParams } from 'react-router-dom';

// --- 1. REGISTER KOMPONEN CHART ---
ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, BarElement, ScatterController, PieController, ArcElement,
  Title, Tooltip, Legend
);

const API_BASE_URL = 'http://localhost:8000/api/stats'; 

// --- 2. WARNA VISUALISASI ---
const clusterColors = [
  'rgba(59, 130, 246, 0.8)', // Biru
  'rgba(72, 187, 120, 0.8)', // Hijau
  'rgba(239, 68, 68, 0.8)',  // Merah
];
const clusterBorderColors = [ 
  '#3b82f6',
  '#48bb78',
  '#ef4444'
];

const Analytics = () => {
  // --- 3. STATE MANAGEMENT ---
  const [violationData, setViolationData] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [importanceData, setImportanceData] = useState(null);
  const [clusterAPIData, setClusterAPIData] = useState(null);
  
  const [loading, setLoading] = useState(true);
  const [searchParams] = useSearchParams();

  // --- 4. DATA MANUAL (HARDCODED) UNTUK KARTU & TABEL ---
  
  const clusterSummaryData = [
    {
      id: 0,
      colorHex: '#3b82f6', // Biru
      title: "Cluster 0: Kepatuhan SLA Sedang",
      size: "35,955 (72.2%)",
      item: "ETP (13%)",
      hour: "09:00 (16.5%)",
      sla: "0.25 – 1.00 (Avg 0.40%)",
      res_time: "3.13 – 10.78 (Avg. 5.49 Hari)",
      insight: "Mayoritas tiket masuk di sini. Performa stabil dengan volume tinggi di jam kerja pagi."
    },
    {
      id: 1,
      colorHex: '#ef4444', // Merah
      title: "Cluster 1: Kepatuhan SLA Rendah",
      size: "9,295 (18.7%)",
      item: "Network (26.2%)",
      hour: "09:00 (12.6%)",
      sla: "0.00 – 0.39 (Avg 0.22%) ⚠️",
      res_time: "3.39 – 28.05 (Avg 6.17 Hari)",
      insight: "SLA terendah dan waktu resolusi terlama. Perlu investigasi khusus pada Application 268."
    },
    {
      id: 2,
      colorHex: '#10b981', // Hijau
      title: "Cluster 2: Kepatuhan SLA Tinggi",
      size: "4,586 (9.2%)",
      item: "One Credit Card ",
      hour: "18:00 (15.8%)",
      sla: "0.17 – 1.00 (Avg 0.43%) ✅",
      res_time: "3.53 – 10.78 (Avg 5.53 Hari)",
      insight: "Tiket sore hari dengan penanganan paling efisien dan kepatuhan SLA tertinggi."
    }
  ];

  const categoricalComparisonData = [
    { feature: "Item (Dominan)", c0: "ETP (13%)", c1: "Network (26.2%)", c2: "One Credit Card (12,6%)" },
    { feature: "Creation Day", c0: "Monday (23.8%)", c1: "Monday (20.1%)", c2: "Tuesday (16,8%)" },
    { feature: "Creation Hour", c0: "09:00 (16.5%)", c1: "09:00 (12.6%)", c2: "18:00 (15.8%)" },
    { feature: "SLA Deadline Day", c0: "Monday (23.8%)", c1: "Friday (23,7%)", c2: "Friday (30.3%)" },
    { feature: "Open Month", c0: "July (15.8%)", c1: "July (11.3%)", c2: "February (14.1%)" }
  ];

  // --- 5. FETCH DATA API ---
  
  const filters = useMemo(() => {
    return `?priority=${searchParams.get('priority') || 'all'}&is_sla_violated=${searchParams.get('is_sla_violated') || 'all'}`;
  }, [searchParams]);

  useEffect(() => {
    const fetchData = async () => {
      // 1. AMBIL TOKEN DARI LOCAL STORAGE
      const token = localStorage.getItem('token'); 
      
      // 2. SIAPKAN HEADERS
      const headers = {
        'Authorization': `Token ${token}`, // <--- INI KUNCINYA
        'Content-Type': 'application/json'
      };

      try {
        // 3. TAMBAHKAN { headers } KE SETIAP FETCH
        const [violRes, trendRes, impRes, clustRes] = await Promise.all([
            fetch(`${API_BASE_URL}/violation-by-category/${filters}`, { headers }),
            fetch(`${API_BASE_URL}/monthly-trend/${filters}`, { headers }),
            fetch(`${API_BASE_URL}/feature-importance/`, { headers }),
            fetch(`http://localhost:8000/api/clusters/`, { headers })
        ]);

        // Cek jika token expired atau tidak valid (401)
        if (violRes.status === 401 || trendRes.status === 401) {
            alert("Sesi habis, silakan login ulang.");
            window.location.href = '/'; // Redirect ke login
            return;
        }

        const vData = await violRes.json();
        const tData = await trendRes.json();
        const iData = await impRes.json();
        const cData = await clustRes.json();

        setViolationData(processViolationData(vData));
        setTrendData(processTrendData(tData));
        setImportanceData(processImportanceData(iData));
        setClusterAPIData(cData);
        setLoading(false);

      } catch (err) {
        console.error("Error fetching data:", err);
        setLoading(false); 
      }
    };
    fetchData();
  }, [filters]);

  // --- 6. FUNGSI PROSES DATA STATISTIK UMUM ---

  const processViolationData = (data) => {
    if (!data?.length) return null;
    const sorted = [...data].sort((a, b) => b.violation_rate - a.violation_rate);
    return {
      labels: sorted.map(d => d.category),
      datasets: [{
        label: 'Pelanggaran SLA (%)',
        data: sorted.map(d => d.violation_rate),
        backgroundColor: 'rgba(239, 68, 68, 0.7)',
        borderRadius: 4,
      }]
    };
  };

  const processTrendData = (data) => {
    if (!data?.length) return null;
    return {
      labels: data.map(d => d.month),
      datasets: [
        { label: 'Total Tiket', data: data.map(d => d.total_tickets), borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.5)', tension: 0.3 },
        { label: 'Melanggar SLA', data: data.map(d => d.violated_tickets), borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.5)', tension: 0.3 }
      ]
    };
  };

  const processImportanceData = (data) => {
    if (!data?.length) return null;
    const sorted = [...data].sort((a, b) => b.importance - a.importance);
    return {
      labels: sorted.map(d => d.feature),
      datasets: [{
        label: 'Importance Score',
        data: sorted.map(d => d.importance),
        backgroundColor: 'rgba(16, 185, 129, 0.7)',
        indexAxis: 'y',
        borderRadius: 4,
      }]
    };
  };

  // --- 7. MEMO DATA UNTUK SCATTER & CLUSTER CHARTS (DINAMIS) ---
  
  // A. Scatter Plots
  const visualScatterData = useMemo(() => {
    if (!clusterAPIData?.visual_scatter?.datasets) return null;
    return {
      datasets: clusterAPIData.visual_scatter.datasets.map((ds, index) => ({
        ...ds,
        backgroundColor: clusterColors[index % clusterColors.length],
        label: `Cluster ${index}` 
      }))
    };
  }, [clusterAPIData]);

  const pcaScatterData = useMemo(() => {
    if (!clusterAPIData?.pca_scatter?.datasets) return null;
    return {
      datasets: clusterAPIData.pca_scatter.datasets.map((ds, index) => ({
        ...ds,
        backgroundColor: clusterColors[index % clusterColors.length],
        label: `Cluster ${index}` 
      }))
    };
  }, [clusterAPIData]);

  const mcaScatterData = useMemo(() => {
    if (!clusterAPIData?.mca_scatter?.datasets) return null;
    return {
      datasets: clusterAPIData.mca_scatter.datasets.map((ds, index) => ({
        ...ds,
        backgroundColor: clusterColors[index % clusterColors.length],
        label: `Cluster ${index}` 
      }))
    };
  }, [clusterAPIData]);

  // B. Cluster Comparison Charts
  const meanBarNumericalData = useMemo(() => {
    if (!clusterAPIData?.mean_bar_numerical?.datasets) return null; 
    const top_cols = clusterAPIData.numerical_columns?.slice(0, 5) || [];
    return {
      labels: clusterAPIData.mean_bar_numerical.labels,
      datasets: clusterAPIData.mean_bar_numerical.datasets
        .filter(ds => top_cols.includes(ds.label))
        .map((ds, index) => ({
          ...ds,
          backgroundColor: `hsl(${index * 60}, 70%, 60%)`,
          borderRadius: 4
      }))
    };
  }, [clusterAPIData]);

  const clusterSizePieData = useMemo(() => {
    if (!clusterAPIData?.cluster_size_pie?.datasets) return null;
    return clusterAPIData.cluster_size_pie; 
  }, [clusterAPIData]);

  // C. Advanced Metrics
  const clusterComplianceBarData = useMemo(() => {
    if (!clusterAPIData?.sla_compliance_bar?.datasets) return null; 
    return {
      labels: clusterAPIData.sla_compliance_bar.labels,
      datasets: clusterAPIData.sla_compliance_bar.datasets.map((ds) => ({
        ...ds,
        backgroundColor: clusterColors,
        borderRadius: 6
      }))
    };
  }, [clusterAPIData]);

  const clusterResolutionBarData = useMemo(() => {
    if (!clusterAPIData?.resolution_time_bar?.datasets) return null; 
    return {
      labels: clusterAPIData.resolution_time_bar.labels,
      datasets: clusterAPIData.resolution_time_bar.datasets.map((ds) => ({
        ...ds,
        backgroundColor: clusterColors,
        borderRadius: 6
      }))
    };
  }, [clusterAPIData]);

  const centroidScatterData = useMemo(() => {
    if (!clusterAPIData?.centroid_scatter?.datasets) return null; 
    return {
      datasets: clusterAPIData.centroid_scatter.datasets.map((ds, index) => ({
        ...ds,
        backgroundColor: clusterColors[index % clusterColors.length],
        pointRadius: 10,
        label: `Centroid Cluster ${index}`
      }))
    };
  }, [clusterAPIData]);

  // D. App Doughnut (Derived from Pie Data)
  const clusterApplicationData = useMemo(() => {
    if (!clusterSizePieData) return null;
    return {
        labels: clusterSizePieData.labels, 
        datasets: clusterSizePieData.datasets.map(ds => ({
            ...ds,
            backgroundColor: clusterColors,
            borderColor: '#fff',
            borderWidth: 2
        }))
    };
  }, [clusterSizePieData]);

  // --- 8. OPSI CHART (OPTIONS) ---
  
  const barOptions = { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } } };
  const lineOptions = { responsive: true, maintainAspectRatio: false };
  const scatterOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: true, position: 'top' } },
    scales: { x: { grid: { display: false } }, y: { grid: { display: false } } },
  };
  const slaResBarOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } }, x: { grid: { display: false } } }
  };
  const pieOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } };

  // --- 9. RENDER UTAMA ---
  return (
    <section id="analytics" className="content-section active" style={{paddingBottom: '60px'}}>
      {loading ? <div className="text-center p-10" style={{color: '#64748b'}}>Memuat data analitik...</div> : (
        <>
          {/* --- BAGIAN 1: STATISTIK UMUM --- */}
          <div className="chart-grid">
            <div className="chart-container" style={{height: '350px'}}>
              <h4 style={{marginBottom: '15px', color: '#1e293b'}}>Pelanggaran per Kategori</h4>
              {violationData ? <Bar data={violationData} options={barOptions} /> : <p>Data tidak tersedia</p>}
            </div>
            <div className="chart-container" style={{height: '350px'}}>
              <h4 style={{marginBottom: '15px', color: '#1e293b'}}>Tren Bulanan</h4>
              {trendData ? <Line data={trendData} options={lineOptions} /> : <p>Data tidak tersedia</p>}
            </div>
            <div className="chart-container" style={{height: '350px'}}>
              <h4 style={{marginBottom: '15px', color: '#1e293b'}}>Fitur Paling Berpengaruh (RF)</h4>
              {importanceData ? <Bar data={importanceData} options={barOptions} /> : <p>Data tidak tersedia</p>}
            </div>
          </div>

          <hr style={{margin: '50px 0', borderTop: '2px dashed #cbd5e1'}} />
          
          <h3 style={{textAlign: 'center', marginBottom: '40px', color: '#0f172a', fontSize: '1.5rem', fontWeight: 'bold'}}>
            🔍 Analisis Segmentasi (K-Prototypes)
          </h3>

          {/* --- BAGIAN 2: SCATTER PLOTS (DINAMIS) --- */}
          <div className="chart-grid">
            <div className="chart-container" style={{height: '400px'}}>
               <h4 style={{color: '#1e293b'}}>Distribusi Hybrid (UMAP)</h4>
               {visualScatterData ? <Scatter data={visualScatterData} options={scatterOptions} /> : <p>Menunggu data...</p>}
            </div>
            <div className="chart-container" style={{height: '400px'}}>
               <h4 style={{color: '#1e293b'}}>Pola Numerik (PCA)</h4>
               {pcaScatterData ? <Scatter data={pcaScatterData} options={scatterOptions} /> : <p>Menunggu data...</p>}
            </div>
            <div className="chart-container" style={{height: '400px'}}>
               <h4 style={{color: '#1e293b'}}>Pola Kategorikal (MCA)</h4>
               {mcaScatterData ? <Scatter data={mcaScatterData} options={scatterOptions} /> : <p>Menunggu data...</p>}
            </div>
          </div>

          {/* --- BAGIAN 3: PROFIL CLUSTER (DINAMIS) --- */}
          <div className="chart-grid" style={{marginTop: '30px'}}>
            {/* Mean Bar */}
            <div className="chart-container" style={{height: '400px'}}>
                <h4 style={{color: '#1e293b'}}>Rata-rata Fitur Numerik (Top 5)</h4>
                {meanBarNumericalData ? <Bar data={meanBarNumericalData} options={barOptions} /> : <p>Data tidak tersedia</p>}
            </div>
             {/* Pie Size */}
             <div className="chart-container" style={{height: '400px'}}>
                <h4 style={{color: '#1e293b'}}>Ukuran Cluster Berdasarkan Item</h4>
                {clusterSizePieData ? <Pie data={clusterSizePieData} options={pieOptions} /> : <p>Data tidak tersedia</p>}
            </div>
             {/* SLA Compliance */}
             <div className="chart-container" style={{height: '400px'}}>
                <h4 style={{color: '#1e293b'}}>SLA Compliance Rate (%)</h4>
                {clusterComplianceBarData ? <Bar data={clusterComplianceBarData} options={{...slaResBarOptions, scales:{y:{max:50, beginAtZero:true}}}} /> : <p>Data tidak tersedia</p>}
            </div>
             {/* Res Time */}
             <div className="chart-container" style={{height: '400px'}}>
                <h4 style={{color: '#1e293b'}}>Avg Resolution Time (Menit)</h4>
                {clusterResolutionBarData ? <Bar data={clusterResolutionBarData} options={slaResBarOptions} /> : <p>Data tidak tersedia</p>}
            </div>
            {/* Centroid Scatter */}
            <div className="chart-container" style={{height: '400px'}}>
                <h4 style={{color: '#1e293b'}}>Centroid: Due vs Duration</h4>
                {centroidScatterData ? <Scatter data={centroidScatterData} options={{...scatterOptions, plugins:{legend:{position:'bottom'}}}} /> : <p>Data tidak tersedia</p>}
            </div>
             {/* App Doughnut */}
             <div className="chart-container" style={{height: '400px'}}>
                <h4 style={{color: '#1e293b'}}>Distribusi Aplikasi</h4>
                {clusterApplicationData ? <Doughnut data={clusterApplicationData} options={pieOptions} /> : <p>Data tidak tersedia</p>}
            </div>
          </div>

          <div style={{height: '40px'}}></div>

          {/* {--- BAGIAN 4: KARTU DETAIL CLUSTER (MANUAL) --- */}
          <div className="cluster-cards-grid">
            {clusterSummaryData.map((cluster) => (
              <div key={cluster.id} className="cluster-card" style={{
                background: `linear-gradient(135deg, ${cluster.colorHex}, rgba(15, 23, 42, 0.9))`,
                color: 'white',
                boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.15)',
                padding: '25px',
                borderRadius: '16px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}>
                <div>
                    <h4 style={{borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: '12px', marginBottom: '15px', fontSize: '1.1rem'}}>
                        {cluster.title}
                    </h4>
                    <div style={{fontSize: '0.95rem', lineHeight: '1.8', opacity: 0.95}}>
                        <p><strong>📦 Size:</strong> {cluster.size}</p>
                        <p><strong>⭐ Item:</strong> {cluster.item}</p>
                        <p><strong>⏰ Jam:</strong> {cluster.hour}</p>
                        <p><strong>✅ SLA Rate:</strong> {cluster.sla}</p>
                        <p><strong>⏱️ Avg Res:</strong> {cluster.res_time}</p>
                    </div>
                </div>
                <div style={{marginTop: '20px', padding: '12px', background: 'rgba(0,0,0,0.25)', borderRadius: '10px', fontSize: '0.85rem', fontStyle: 'italic', borderLeft: '4px solid rgba(255,255,255,0.4)'}}>
                    "{cluster.insight}"
                </div>
              </div>
            ))}
          </div> 

          {/* --- BAGIAN 5: TABEL PERBANDINGAN --- */}
          <div style={{ marginTop: '50px', overflowX: 'auto', padding: '0 5px' }}>
            <h4 style={{ color: '#334155', marginBottom: '20px', textAlign: 'center', fontWeight: '600' }}>
                📋 Perbandingan Modus Fitur Kategorikal
            </h4>
            <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
              <thead>
                <tr style={{ background: '#1e293b', color: 'white' }}>
                  <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600' }}>Fitur</th>
                  <th style={{ padding: '16px', textAlign: 'center', borderLeft: '1px solid #475569' }}>Cluster 0</th>
                  <th style={{ padding: '16px', textAlign: 'center', borderLeft: '1px solid #475569' }}>Cluster 1</th>
                  <th style={{ padding: '16px', textAlign: 'center', borderLeft: '1px solid #475569' }}>Cluster 2</th>
                </tr>
              </thead>
              <tbody>
                {categoricalComparisonData.map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0', background: idx % 2 === 0 ? '#f8fafc' : 'white' }}>
                    <td style={{ padding: '14px 16px', fontWeight: '600', color: '#334155' }}>{row.feature}</td>
                    <td style={{ padding: '14px', textAlign: 'center', color: '#475569' }}>{row.c0}</td>
                    <td style={{ padding: '14px', textAlign: 'center', color: '#475569' }}>{row.c1}</td>
                    <td style={{ padding: '14px', textAlign: 'center', color: '#475569' }}>{row.c2}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

        </>
      )}
    </section>
  );
};

export default Analytics;