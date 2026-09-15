import React from 'react'
import ReactDOM from 'react-dom/client'
import { Activity, Bell, FileText, GitBranch, LayoutDashboard, Settings, ShieldCheck, Users } from 'lucide-react'
import './styles.css'

const menu = [
  [LayoutDashboard, 'Dashboard'], [Users, 'Pengguna'], [ShieldCheck, 'Role & Permission'],
  [GitBranch, 'Workflow'], [FileText, 'Template Dokumen'], [Activity, 'Audit Log'], [Settings, 'Konfigurasi'],
] as const

function App() {
  return <div className="shell">
    <aside>
      <div className="brand"><span>SD</span><div>SmartDispo<small>DPRD Kota Bitung</small></div></div>
      <nav>{menu.map(([Icon, label], index) => <button className={index === 0 ? 'active' : ''} key={label}><Icon size={19}/>{label}</button>)}</nav>
    </aside>
    <main>
      <header><div><h1>Dashboard</h1><p>Ringkasan workflow persuratan hari ini</p></div><div className="profile"><Bell size={20}/><span>Administrator</span></div></header>
      <section className="metrics">
        <Metric value="18" label="Dokumen diproses" tone="green"/>
        <Metric value="7" label="Tugas menunggu" tone="gold"/>
        <Metric value="2" label="Dikembalikan" tone="red"/>
        <Metric value="124" label="Selesai bulan ini" tone="blue"/>
      </section>
      <section className="grid">
        <article className="panel"><div className="panel-title"><h2>Aktivitas workflow</h2><button>Lihat semua</button></div>
          <table><thead><tr><th>Dokumen</th><th>Unit</th><th>Status</th><th>Diperbarui</th></tr></thead>
          <tbody><Row doc="PD-2026-00123" unit="Komisi I" status="Menunggu paraf"/><Row doc="SM-2026-00318" unit="Tata Usaha" status="Disposisi Ketua"/><Row doc="RP-2026-00042" unit="Bapemperda" status="Verifikasi"/></tbody></table>
        </article>
        <article className="panel workflow"><div className="panel-title"><h2>Workflow aktif</h2></div>
          {['Permintaan Perjalanan Dinas','Surat Masuk Ketua','Surat Masuk Sekretaris','Permintaan Rapat'].map((name, i) => <div className="flow" key={name}><span>{name}</span><b>v{i+1} · Published</b></div>)}
        </article>
      </section>
    </main>
  </div>
}

function Metric({value,label,tone}:{value:string,label:string,tone:string}) { return <article className={`metric ${tone}`}><strong>{value}</strong><span>{label}</span></article> }
function Row({doc,unit,status}:{doc:string,unit:string,status:string}) { return <tr><td><b>{doc}</b></td><td>{unit}</td><td><span className="badge">{status}</span></td><td>Baru saja</td></tr> }

ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>)
