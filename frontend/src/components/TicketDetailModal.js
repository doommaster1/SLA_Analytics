
const TicketDetailModal = ({ ticket, onClose }) => {
  if (!ticket) return null;

  // --- HELPER FUNCTIONS ---
  const safeFixed = (val, digits = 2) => {
    if (val === null || val === undefined) return 'N/A';
    return Number(val).toFixed(digits);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString('id-ID', {
      day: 'numeric', month: 'long', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const getPriorityClass = (priority) => {
    if (!priority) return 'badge-low';
    if (priority.includes('High')) return 'badge-high';
    if (priority.includes('Medium')) return 'badge-medium';
    if (priority.includes('Critical')) return 'badge-critical';
    return 'badge-low';
  };

  const ticketStatus = ticket.status || (ticket.closed_date ? 'Closed' : 'Open');
  const violatedClass = ticket.is_sla_violated ? 'violated' : 'safe';
  const violationText = ticket.sla_violated_text || (ticket.is_sla_violated ? 'Melanggar SLA' : 'SLA Aman');

  return (
    <div className="modal show" onClick={onClose}>
      {/* Stop Propagation agar klik di dalam modal tidak menutup modal */}
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        
        {/* HEADER: Tetap di atas (Sticky) */}
        <div className="modal-header">
          <h2>Detail Tiket #{ticket.number}</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        {/* BODY: Bagian ini yang akan di-scroll */}
        <div className="modal-body">
            
            <div className="ticket-info">
              <p><strong>Item:</strong> {ticket.item || '-'}</p>
              <p><strong>Kategori:</strong> {ticket.category || '-'}</p>
              <span className={`badge ${getPriorityClass(ticket.priority)}`}>
                {ticket.priority || 'Unknown'}
              </span>
            </div>

            <div className="detail-grid">
              <div className={`detail-item ${violatedClass}`}>
                <h4>Status SLA</h4>
                <p style={{ fontWeight: 'bold' }}>{violationText}</p>
              </div>
              <div className="detail-item">
                <h4>Resolution Duration</h4>
                <p>{safeFixed(ticket.resolution_duration, 2)} Hari</p>
              </div>
              <div className="detail-item">
                <h4>SLA Threshold</h4>
                <p>{safeFixed(ticket.sla_threshold, 1)} Jam</p>
              </div>
              <div className="detail-item">
                <h4>Avg Resolution Time (Ac)</h4>
                <p>{safeFixed(ticket.average_resolution_time_ac, 2)} Jam</p>
              </div>
              <div className="detail-item">
                <h4>Total Tickets (Wc)</h4>
                <p>{safeFixed(ticket.total_tickets_resolved_wc, 1)}</p>
              </div>
              <div className="detail-item">
                <h4>SLA to Avg Ratio (Rc)</h4>
                <p>{safeFixed(ticket.sla_to_average_resolution_ratio_rc, 3)}</p>
              </div>
              <div className="detail-item">
                <h4>App SLA Compliance</h4>
                <p>
                    {ticket.compliance_rate_percent 
                      ? ticket.compliance_rate_percent 
                      : (ticket.application_sla_compliance_rate 
                          ? (ticket.application_sla_compliance_rate * 100).toFixed(1) + '%' 
                          : 'N/A')
                    }
                </p>
              </div>
              <div className="detail-item">
                <h4>Confidence Score</h4>
                <p>{ticket.confidence_score ? (ticket.confidence_score * 100).toFixed(1) + '%' : 'N/A'}</p>
              </div>
            </div>

            <div className="metrics-section">
              <h3>Informasi Waktu & Status</h3>
              <div className="metrics-row">
                <span className="metrics-label">Waktu Dibuka:</span>
                <span className="metrics-value">{formatDate(ticket.open_date)}</span>
              </div>
              <div className="metrics-row">
                <span className="metrics-label">Waktu Ditutup:</span>
                <span className="metrics-value">{formatDate(ticket.closed_date)}</span>
              </div>
              <div className="metrics-row">
                <span className="metrics-label">Due Date:</span>
                <span className="metrics-value">{formatDate(ticket.due_date)}</span>
              </div>
              <div className="metrics-row">
                <span className="metrics-label">Status:</span>
                <span className="metrics-value" style={{ fontWeight: 'bold', color: ticketStatus === 'Closed' ? 'green' : '#d97706' }}>
                    {ticketStatus}
                </span>
              </div>
              {ticket.assigned_to && (
                 <div className="metrics-row">
                    <span className="metrics-label">Assigned To:</span>
                    <span className="metrics-value">{ticket.assigned_to}</span>
                 </div>
              )}
              {ticket.root_cause && (
                 <div className="metrics-row">
                    <span className="metrics-label">Root Cause:</span>
                    <span className="metrics-value">{ticket.root_cause}</span>
                 </div>
              )}
            </div>

        </div> 
      </div>
    </div>
  );
};

export default TicketDetailModal;