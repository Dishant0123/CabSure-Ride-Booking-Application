const state = { token: sessionStorage.getItem('cabsure-admin-token'), admin: JSON.parse(sessionStorage.getItem('cabsure-admin-profile') || 'null'), page: 'overview' };
const loginView = document.querySelector('#login-view');
const appView = document.querySelector('#app-view');
const content = document.querySelector('#page-content');
const error = document.querySelector('#app-error');

const api = async (path, options = {}) => {
  const response = await fetch(`/api/v1${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}), ...(options.headers || {}) } });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) { const detail = Array.isArray(body.detail) ? body.detail.map(item => item.msg).join(' ') : body.detail; throw new Error(detail || 'The request could not be completed.'); }
  return body;
};
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
const badge = value => `<span class="badge ${esc(value)}">${esc(value).replaceAll('_', ' ')}</span>`;
const localPhone = value => String(value ?? '').replace(/\D/g, '').slice(-10);
const has = permission => state.admin?.permissions?.includes(permission);

function showApp() {
  loginView.classList.add('hidden'); appView.classList.remove('hidden');
  document.querySelector('#admin-name').textContent = `${state.admin.full_name} · ID ${state.admin.id}`;
  document.querySelector('#admin-role').textContent = state.admin.role.replaceAll('_', ' ');
  document.querySelector('[data-page="documents"]').classList.toggle('hidden', !has('documents:review'));
  document.querySelector('[data-page="support"]').classList.toggle('hidden', !has('support:manage'));
  document.querySelector('[data-page="outstation"]').classList.toggle('hidden', !has('outstation:manage'));
  render();
}
function showLogin() { appView.classList.add('hidden'); loginView.classList.remove('hidden'); }
function clearSession() { sessionStorage.clear(); state.token = null; state.admin = null; showLogin(); }

document.querySelector('#login-form').addEventListener('submit', async event => {
  event.preventDefault(); const loginError = document.querySelector('#login-error'); const button = event.currentTarget.querySelector('button'); loginError.textContent = ''; button.disabled = true; button.textContent = 'Checking Admin ID...';
  try { const session = await api('/admin/auth/login', { method: 'POST', body: JSON.stringify({ email: document.querySelector('#email').value, password: document.querySelector('#password').value }) }); state.token = session.access_token; state.admin = session.admin; sessionStorage.setItem('cabsure-admin-token', state.token); sessionStorage.setItem('cabsure-admin-profile', JSON.stringify(state.admin)); showApp(); }
  catch (err) { loginError.textContent = err.message; }
  finally { button.disabled = false; button.textContent = 'Sign in securely'; }
});
document.querySelector('#logout').addEventListener('click', clearSession);
document.querySelectorAll('.nav-item').forEach(button => button.addEventListener('click', () => { state.page = button.dataset.page; document.querySelectorAll('.nav-item').forEach(item => item.classList.toggle('active', item === button)); render(); }));

async function render() {
  error.textContent = ''; document.querySelector('#page-title').textContent = ({ overview: 'Overview', documents: 'Document reviews', drivers: 'Drivers & vehicles', support: 'Support tickets', outstation: 'Outstation bookings', account: 'Admin account' })[state.page]; content.innerHTML = '<p class="empty">Loading...</p>';
  try { if (state.page === 'overview') await overview(); if (state.page === 'documents') await documents(); if (state.page === 'drivers') await drivers(); if (state.page === 'support') await support(); if (state.page === 'outstation') await outstation(); if (state.page === 'account') await account(); }
  catch (err) { content.innerHTML = ''; error.textContent = err.message; if (/Admin session|authentication|unavailable/i.test(err.message)) clearSession(); }
}
async function overview() {
  const [docs, driverList, tickets] = await Promise.all([has('documents:review') ? api('/admin/driver-documents?status_filter=pending') : [], api('/admin/drivers'), has('support:manage') ? api('/admin/support-tickets?ticket_status=open') : []]);
  content.innerHTML = `<div class="metrics"><div class="metric"><span>Pending documents</span><strong>${docs.length}</strong></div><div class="metric"><span>Drivers</span><strong>${driverList.length}</strong></div><div class="metric"><span>Verified vehicles</span><strong>${driverList.filter(driver => driver.vehicle_verification_status === 'verified').length}</strong></div><div class="metric"><span>Open support tickets</span><strong>${tickets.length}</strong></div></div><div class="page-grid"><section class="panel"><h2>Next action</h2><p class="muted">Review pending Driver documents to move eligible vehicles into the approved fleet.</p></section><section class="panel"><h2>Secure operations</h2><p class="muted">Your Admin role controls every available action. Sensitive changes are audited.</p></section></div>`;
}
async function documents() {
  const items = await api('/admin/driver-documents?status_filter=pending');
  content.innerHTML = items.length ? `<div class="list">${items.map(item => `<article class="item"><div class="item-head"><h3>${esc(item.driver_name)} · ${esc(labelDocument(item.document_type))}</h3>${badge(item.verification_status)}</div><p>${esc(item.operating_city || 'City not provided')} · Vehicle: ${esc(item.vehicle_registration_number || 'Not assigned')}</p><p>Document number: ${esc(item.document_number)}</p><div class="actions"><button class="approve" data-review="verified" data-driver="${item.driver_id}" data-document="${item.document_type}">Approve</button><button class="reject" data-review="rejected" data-driver="${item.driver_id}" data-document="${item.document_type}">Reject</button></div></article>`).join('')}</div>` : '<div class="panel empty">No pending documents to review.</div>';
  document.querySelectorAll('[data-review]').forEach(button => button.addEventListener('click', () => reviewDocument(button.dataset.driver, button.dataset.document, button.dataset.review)));
}
async function reviewDocument(driverId, documentType, decision) { const review_note = decision === 'rejected' ? prompt('Explain why this document is rejected:') : null; if (decision === 'rejected' && !review_note) return; try { await api(`/admin/drivers/${driverId}/documents/${documentType}/review`, { method: 'PUT', body: JSON.stringify({ status: decision, review_note }) }); await documents(); } catch (err) { error.textContent = err.message; } }
async function drivers() {
  const items = await api('/admin/drivers');
  content.innerHTML = items.length ? `<div class="panel table-wrap"><table class="table"><thead><tr><th>Driver</th><th>City</th><th>Vehicle</th><th>Vehicle status</th><th>Documents</th></tr></thead><tbody>${items.map(item => `<tr><td><strong>${esc(item.full_name)}</strong><br><span class="muted">${esc(localPhone(item.phone_number))}</span></td><td>${esc(item.operating_city || '—')}</td><td>${esc(item.vehicle_name || '—')}<br><span class="muted">${esc(item.vehicle_registration_number || '')}</span></td><td>${item.vehicle_verification_status ? badge(item.vehicle_verification_status) : '—'}</td><td>${Object.values(item.document_statuses).map(badge).join(' ') || '—'}</td></tr>`).join('')}</tbody></table></div>` : '<div class="panel empty">No Drivers are registered yet.</div>';
}
async function support() {
  const items = await api('/admin/support-tickets');
  content.innerHTML = items.length ? `<div class="list">${items.map(item => `<article class="item"><div class="item-head"><h3>${esc(item.subject)}</h3>${badge(item.status)}</div><p>${esc(item.passenger_name)} · ${esc(item.category)} · ${new Date(item.created_at).toLocaleDateString()}</p><p>${esc(item.description)}</p>${item.resolution_note ? `<p><strong>Resolution:</strong> ${esc(item.resolution_note)}</p>` : ''}<div class="actions"><button class="secondary" data-ticket="${item.id}" data-status="in_progress">Mark in progress</button><button class="approve" data-ticket="${item.id}" data-status="resolved">Resolve</button></div></article>`).join('')}</div>` : '<div class="panel empty">No support tickets require action.</div>';
  document.querySelectorAll('[data-ticket]').forEach(button => button.addEventListener('click', () => updateTicket(button.dataset.ticket, button.dataset.status)));
}
async function updateTicket(ticketId, status) { const resolution_note = status === 'resolved' ? prompt('Add a resolution note:') : null; if (status === 'resolved' && !resolution_note) return; try { await api(`/admin/support-tickets/${ticketId}`, { method: 'PATCH', body: JSON.stringify({ status, resolution_note }) }); await support(); } catch (err) { error.textContent = err.message; } }
async function outstation() {
  const items = await api('/admin/outstation-bookings');
  content.innerHTML = items.length ? `<div class="list">${items.map(item => `<article class="item outstation-item"><div class="item-head"><h3>Booking #${item.id} · ${esc(item.passenger_name)}</h3>${badge(item.status)}</div><div class="booking-flow">${['Request','Confirm','Assign driver'].map((label,index) => `<span class="${outstationStage(item.status) >= index ? 'done' : ''}"><b>${index + 1}</b>${label}</span>`).join('')}</div><p>${esc(localPhone(item.passenger_phone_number))} · ${new Date(item.scheduled_at).toLocaleString('en-IN')}</p><p><strong>${esc(item.pickup_address)}</strong> → <strong>${esc(item.destination_address)}</strong></p><p>Preference: ${esc(item.preferred_vehicle_type || 'Any car')} · ${item.estimated_distance_km ? `${item.estimated_distance_km} km routed` : 'Route unavailable'} · ${item.estimated_fare_paise ? `Estimated ₹${Math.round(item.estimated_fare_paise / 100).toLocaleString('en-IN')}` : 'Estimate unavailable'}</p>${item.driver_name ? `<div class="assigned-driver"><strong>${esc(item.driver_name)}</strong><span>${esc(localPhone(item.driver_phone_number))} · ${esc(item.vehicle_name)} · ${esc(item.vehicle_registration_number)}</span></div>` : ''}<div class="actions">${item.status === 'requested' ? `<button class="approve" data-outstation="confirm" data-id="${item.id}">Confirm request &amp; estimate</button><button class="reject" data-outstation="reject" data-id="${item.id}">Reject</button>` : ''}${item.status === 'confirmed' ? `<button class="approve" data-outstation="assign" data-id="${item.id}">Choose eligible driver</button>` : ''}${item.status === 'driver_assigned' ? `<button class="secondary" data-outstation="complete" data-id="${item.id}">Mark completed</button>` : ''}</div></article>`).join('')}</div>` : '<div class="panel empty">No outstation bookings require attention.</div>';
  document.querySelectorAll('[data-outstation]').forEach(button => button.addEventListener('click', () => button.dataset.outstation === 'assign' ? openDriverPicker(Number(button.dataset.id)) : updateOutstation(Number(button.dataset.id), button.dataset.outstation)));
}
function outstationStage(status) { return status === 'requested' ? 0 : status === 'confirmed' ? 1 : ['driver_assigned','completed'].includes(status) ? 2 : -1; }
async function openDriverPicker(bookingId) {
  try {
    const drivers = await api(`/admin/outstation-bookings/${bookingId}/eligible-drivers`);
    const overlay = document.createElement('div'); overlay.className = 'modal-overlay';
    overlay.innerHTML = `<section class="driver-picker" role="dialog" aria-modal="true"><div class="picker-head"><div><p class="eyebrow">BOOKING #${bookingId}</p><h2>Choose an eligible driver</h2><p class="muted">Only active drivers with verified vehicles and no schedule conflict are shown.</p></div><button class="picker-close" aria-label="Close">×</button></div>${drivers.length ? `<div class="driver-options">${drivers.map(driver => `<article class="driver-option"><div><h3>${esc(driver.full_name)}</h3><p>${esc(driver.phone_number)} · ${esc(driver.operating_city || 'City not set')}</p><p>${esc(driver.vehicle_name)} · ${esc(driver.vehicle_registration_number)} · ${driver.seat_count} seats</p><span>★ ${driver.rating || 'New'} · ${driver.completed_rides} completed rides</span></div><button class="approve" data-assign-phone="${esc(driver.phone_number)}">Assign driver</button></article>`).join('')}</div>` : '<div class="empty">No eligible driver is available for this schedule.</div>'}</section>`;
    document.body.appendChild(overlay);
    const close = () => overlay.remove();
    overlay.addEventListener('click', event => { if (event.target === overlay || event.target.closest('.picker-close')) close(); });
    overlay.querySelectorAll('[data-assign-phone]').forEach(button => button.addEventListener('click', async () => { button.disabled = true; button.textContent = 'Assigning…'; try { await api(`/admin/outstation-bookings/${bookingId}`, { method:'PATCH', body:JSON.stringify({ status:'driver_assigned', driver_phone_number:button.dataset.assignPhone }) }); close(); await outstation(); } catch (err) { button.disabled = false; button.textContent = 'Assign driver'; error.textContent = err.message; } }));
  } catch (err) { error.textContent = err.message; }
}
async function updateOutstation(id, action) { let body; if (action === 'confirm') { if (!confirm('Confirm the routed fare estimate and accept this booking for support fulfilment?')) return; body = { status:'confirmed' }; } else if (action === 'reject') { const note = prompt('Reason for rejecting this request:'); if (!note) return; body = { status:'rejected', support_note:note }; } else body = { status:'completed' }; try { await api(`/admin/outstation-bookings/${id}`, { method:'PATCH', body:JSON.stringify(body) }); await outstation(); } catch (err) { error.textContent = err.message; } }
async function account() {
  state.admin = await api('/admin/auth/me'); sessionStorage.setItem('cabsure-admin-profile', JSON.stringify(state.admin));
  content.innerHTML = `<div class="account-grid"><section class="panel"><h2>Admin ID</h2><div class="detail-row"><span class="muted">ID</span><strong>${state.admin.id}</strong></div><div class="detail-row"><span class="muted">Email</span><strong>${esc(state.admin.email)}</strong></div><div class="detail-row"><span class="muted">Role</span>${badge(state.admin.role)}</div><div class="detail-row"><span class="muted">Last login</span><strong>${state.admin.last_login_at ? new Date(state.admin.last_login_at).toLocaleString() : 'First session'}</strong></div><h2>Role permissions</h2><div class="permission-list">${state.admin.permissions.map(permission => badge(permission.replace(':', '_'))).join('')}</div></section><form id="password-form" class="panel account-form"><h2>Security maintenance</h2><p class="muted">Changing your password immediately closes every existing Admin session.</p><label>Current password<input id="current-password" type="password" autocomplete="current-password" minlength="8" required /></label><label>New password<input id="new-password" type="password" autocomplete="new-password" minlength="12" required /></label><label>Confirm new password<input id="confirm-password" type="password" autocomplete="new-password" minlength="12" required /></label><p id="password-error" class="error" role="alert"></p><button class="primary" type="submit">Change password</button></form></div>`;
  document.querySelector('#password-form').addEventListener('submit', changePassword);
}
async function changePassword(event) { event.preventDefault(); const message = document.querySelector('#password-error'); const current = document.querySelector('#current-password').value; const next = document.querySelector('#new-password').value; const confirm = document.querySelector('#confirm-password').value; if (next !== confirm) { message.textContent = 'New passwords do not match.'; return; } const button = event.currentTarget.querySelector('button'); button.disabled = true; try { const result = await api('/admin/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password: current, new_password: next }) }); alert(result.message); clearSession(); } catch (err) { message.textContent = err.message; } finally { button.disabled = false; } }
function labelDocument(value) { return ({ driving_licence: 'Driving licence', vehicle_registration: 'Vehicle registration', aadhaar: 'Aadhaar card', vehicle_insurance: 'Vehicle insurance' })[value] || value; }

if (state.token && state.admin) api('/admin/auth/me').then(profile => { state.admin = profile; sessionStorage.setItem('cabsure-admin-profile', JSON.stringify(profile)); showApp(); }).catch(clearSession); else showLogin();
