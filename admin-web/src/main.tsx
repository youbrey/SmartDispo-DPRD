import React, { FormEvent, useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { Activity, Bell, FileText, GitBranch, LayoutDashboard, LogOut, Settings, ShieldCheck, Users } from 'lucide-react'
import './styles.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
const TOKEN_KEY = 'smartdispo_admin_access_token'

type Profile = { id: string; username: string; full_name: string; permissions: string[] }
type DashboardData = { documents: Record<string, number> }

const menu = [
  [LayoutDashboard, 'Dashboard', true], [Users, 'Pengguna', false], [ShieldCheck, 'Role & Permission', false],
  [GitBranch, 'Workflow', false], [FileText, 'Template Dokumen', false], [Activity, 'Audit Log', false],
  [Settings, 'Konfigurasi', false],
] as const

async function api<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...init?.headers },
  })
  if (!response.ok) throw new Error(response.status === 401 ? 'SESSION_EXPIRED' : await response.text())
  return response.json() as Promise<T>
}

function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) ?? '')
  const [profile, setProfile] = useState<Profile | null>(null)
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [error, setError] = useState('')

  function logout() {
    sessionStorage.removeItem(TOKEN_KEY)
    setToken('')
    setProfile(null)
    setDashboard(null)
  }

  useEffect(() => {
    if (!token) return
    Promise.all([api<Profile>('/auth/me', token), api<DashboardData>('/admin/dashboard', token)])
      .then(([user, data]) => { setProfile(user); setDashboard(data); setError('') })
      .catch((reason: Error) => {
        if (reason.message === 'SESSION_EXPIRED') logout()
        else setError('Dashboard belum dapat dimuat. Periksa backend dan hak akses akun.')
      })
  }, [token])

  if (!token) return <Login onAuthenticated={(accessToken) => {
    sessionStorage.setItem(TOKEN_KEY, accessToken)
    setToken(accessToken)
  }}/>

  const counts = dashboard?.documents ?? {}
  return <div className="shell">
    <aside>
      <div className="brand"><span>SD</span><div>SmartDispo<small>DPRD Kota Bitung</small></div></div>
      <nav>{menu.map(([Icon, label, enabled]) => <button className={enabled ? 'active' : ''} disabled={!enabled} key={label}>
        <Icon size={19}/>{label}{!enabled && <small>Berikutnya</small>}
      </button>)}</nav>
    </aside>
    <main>
      <header>
        <div><h1>Dashboard</h1><p>Data langsung dari workflow SmartDispo</p></div>
        <div className="profile"><Bell size={20}/><span>{profile?.full_name ?? 'Memuat…'}</span><button onClick={logout} title="Keluar"><LogOut size={18}/></button></div>
      </header>
      {error && <div className="alert">{error}</div>}
      <section className="metrics">
        <Metric value={String(counts.IN_PROGRESS ?? 0)} label="Dokumen diproses" tone="green"/>
        <Metric value={String(counts.DRAFT ?? 0)} label="Draft" tone="gold"/>
        <Metric value={String(counts.RETURNED ?? 0)} label="Dikembalikan" tone="red"/>
        <Metric value={String(counts.COMPLETED ?? 0)} label="Dokumen selesai" tone="blue"/>
      </section>
      <section className="grid">
        <article className="panel">
          <div className="panel-title"><h2>Status dokumen</h2><span className="live">● LIVE</span></div>
          <table><thead><tr><th>Status</th><th>Jumlah</th></tr></thead>
            <tbody>{Object.entries(counts).length === 0
              ? <tr><td colSpan={2}>Belum ada dokumen.</td></tr>
              : Object.entries(counts).map(([status, count]) => <tr key={status}><td><span className="badge">{status.replaceAll('_', ' ')}</span></td><td><b>{count}</b></td></tr>)}
            </tbody></table>
        </article>
        <article className="panel">
          <div className="panel-title"><h2>Akses administrator</h2></div>
          <p className="muted">Login dan permission telah diverifikasi oleh backend.</p>
          <div className="permission-count"><strong>{profile?.permissions.length ?? 0}</strong><span>permission efektif</span></div>
          <small className="muted">Modul konfigurasi pengguna dan workflow akan diaktifkan pada tahap berikutnya.</small>
        </article>
      </section>
    </main>
  </div>
}

function Login({ onAuthenticated }: { onAuthenticated: (token: string) => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!username.trim() || !password) return setError('Nama pengguna dan kata sandi wajib diisi.')
    setLoading(true)
    setError('')
    const body = new URLSearchParams({ username: username.trim(), password })
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body,
      })
      if (!response.ok) throw new Error()
      const data = await response.json() as { access_token: string }
      onAuthenticated(data.access_token)
    } catch {
      setError('Login gagal. Periksa akun administrator dan koneksi backend.')
    } finally { setLoading(false) }
  }

  return <div className="login-page"><form className="login-card" onSubmit={submit}>
    <div className="brand login-brand"><span>SD</span><div>SmartDispo<small>DPRD Kota Bitung</small></div></div>
    <h1>Panel Administrator</h1><p>Masuk menggunakan akun yang dibuat pada server.</p>
    <label>Nama pengguna<input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username"/></label>
    <label>Kata sandi<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password"/></label>
    {error && <div className="alert">{error}</div>}
    <button className="primary" disabled={loading}>{loading ? 'Memeriksa…' : 'Masuk'}</button>
  </form></div>
}

function Metric({value,label,tone}:{value:string,label:string,tone:string}) {
  return <article className={`metric ${tone}`}><strong>{value}</strong><span>{label}</span></article>
}

ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>)
