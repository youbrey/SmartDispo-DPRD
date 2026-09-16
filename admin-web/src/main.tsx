import React, { FormEvent, useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { Activity, Bell, FileText, GitBranch, LayoutDashboard, LogOut, Settings, ShieldCheck, Users } from 'lucide-react'
import './styles.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
const TOKEN_KEY = 'smartdispo_admin_access_token'

type Page = 'dashboard' | 'users' | 'roles' | 'workflows' | 'templates' | 'audit'
type Profile = { id: string; username: string; full_name: string; permissions: string[] }
type DashboardData = { documents: Record<string, number>; active_users: number; published_workflows: number }
type UserRow = { id:string; username:string; full_name:string; email?:string; access_level:number; active:boolean; roles:string[] }
type PermissionRow = { id:string; code:string; description:string }
type RoleRow = { id:string; code:string; name:string; system:boolean; permissions:{id:string;code:string}[] }
type WorkflowRow = { id:string; name:string; document_type:string; version:number; state:string; step_count:number }
type AuditRow = { id:string; occurred_at:string; action:string; entity_type:string; entity_id?:string }
type UnitRow = { id:string; code:string; name:string; active:boolean }
type AssignmentRow = { id:string; role_id:string; role_code:string; user_id:string; user_name:string; valid_from:string; valid_until?:string; active:boolean }
type TemplateVersionRow = { id:string; version:number; sha256_hash:string; active:boolean; created_at:string }
type TemplateRow = { id:string; code:string; name:string; versions:TemplateVersionRow[] }

const menu: [Page, React.ElementType, string][] = [
  ['dashboard', LayoutDashboard, 'Dashboard'], ['users', Users, 'Pengguna'],
  ['roles', ShieldCheck, 'Role & Permission'], ['workflows', GitBranch, 'Workflow'],
  ['templates', FileText, 'Template Dokumen'], ['audit', Activity, 'Audit Log'],
]

async function api<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...init?.headers },
  })
  if (!response.ok) throw new Error(response.status === 401 ? 'SESSION_EXPIRED' : await response.text())
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) ?? '')
  const [profile, setProfile] = useState<Profile | null>(null)
  const [page, setPage] = useState<Page>('dashboard')
  const [error, setError] = useState('')

  function logout() {
    sessionStorage.removeItem(TOKEN_KEY); setToken(''); setProfile(null)
  }
  useEffect(() => {
    if (!token) return
    api<Profile>('/auth/me', token).then(setProfile).catch((reason: Error) => {
      if (reason.message === 'SESSION_EXPIRED') logout(); else setError('Profil tidak dapat dimuat.')
    })
  }, [token])

  if (!token) return <Login onAuthenticated={(accessToken) => {
    sessionStorage.setItem(TOKEN_KEY, accessToken); setToken(accessToken)
  }}/>

  const title = menu.find(([key]) => key === page)?.[2] ?? 'SmartDispo'
  return <div className="shell">
    <aside>
      <div className="brand"><span>SD</span><div>SmartDispo<small>DPRD Kota Bitung</small></div></div>
      <nav>{menu.map(([key, Icon, label]) => <button className={page === key ? 'active' : ''} onClick={() => { setPage(key); setError('') }} key={key}>
        <Icon size={19}/>{label}
      </button>)}</nav>
      <nav className="nav-bottom"><button disabled><Settings size={19}/>Konfigurasi</button></nav>
    </aside>
    <main>
      <header><div><h1>{title}</h1><p>Konfigurasi tersimpan langsung pada server SmartDispo</p></div>
        <div className="profile"><Bell size={20}/><span>{profile?.full_name ?? 'Memuat…'}</span><button onClick={logout} title="Keluar"><LogOut size={18}/></button></div>
      </header>
      {error && <div className="alert">{error}</div>}
      {page === 'dashboard' && <Dashboard token={token} fail={setError}/>}
      {page === 'users' && <UsersPage token={token} fail={setError}/>}
      {page === 'roles' && <RolesPage token={token} fail={setError}/>}
      {page === 'workflows' && <WorkflowsPage token={token} fail={setError}/>}
      {page === 'templates' && <TemplatesPage token={token} fail={setError}/>}
      {page === 'audit' && <AuditPage token={token} fail={setError}/>}
    </main>
  </div>
}

function Dashboard({token,fail}:{token:string;fail:(value:string)=>void}) {
  const [data,setData] = useState<DashboardData|null>(null)
  useEffect(() => { api<DashboardData>('/admin/dashboard',token).then(setData).catch(()=>fail('Dashboard belum dapat dimuat.')) },[token])
  const counts=data?.documents??{}
  return <><section className="metrics">
    <Metric value={String(counts.IN_PROGRESS??0)} label="Dokumen diproses" tone="green"/>
    <Metric value={String(counts.DRAFT??0)} label="Draft" tone="gold"/>
    <Metric value={String(data?.active_users??0)} label="Pengguna aktif" tone="blue"/>
    <Metric value={String(data?.published_workflows??0)} label="Workflow aktif" tone="green"/>
  </section><section className="grid"><article className="panel"><div className="panel-title"><h2>Status dokumen</h2><span className="live">● LIVE</span></div>
    <table><thead><tr><th>Status</th><th>Jumlah</th></tr></thead><tbody>{Object.entries(counts).map(([status,count])=><tr key={status}><td><span className="badge">{status.replaceAll('_',' ')}</span></td><td><b>{count}</b></td></tr>)}</tbody></table>
  </article><article className="panel"><h2>Kontrol administrasi</h2><p className="muted">Pengguna, role, permission, pejabat aktif, workflow versi, dan audit dikelola dari menu sebelah kiri.</p></article></section></>
}

function UsersPage({token,fail}:{token:string;fail:(value:string)=>void}) {
  const [rows,setRows]=useState<UserRow[]>([]); const [roles,setRoles]=useState<RoleRow[]>([]); const [show,setShow]=useState(false);const [editingUser,setEditingUser]=useState<UserRow|null>(null)
  const load=()=>Promise.all([api<UserRow[]>('/admin/users',token),api<RoleRow[]>('/admin/roles',token)]).then(([u,r])=>{setRows(u);setRoles(r)}).catch(()=>fail('Data pengguna tidak dapat dimuat.'))
  useEffect(()=>{load()},[token])
  async function toggle(row:UserRow){try{await api(`/admin/users/${row.id}`,token,{method:'PATCH',body:JSON.stringify({active:!row.active})});await load()}catch{fail('Status pengguna gagal diubah.')}}
  async function resetPassword(row:UserRow){const password=window.prompt(`Kata sandi baru untuk ${row.full_name} (minimal 12 karakter)`);if(!password)return;try{await api(`/admin/users/${row.id}/reset-password`,token,{method:'POST',body:JSON.stringify({password})});window.alert('Kata sandi berhasil direset dan sesi lama dibatalkan.')}catch{fail('Reset kata sandi gagal. Pastikan minimal 12 karakter.')}}
  return <section className="panel"><div className="panel-title"><h2>Daftar pengguna</h2><button className="action" onClick={()=>setShow(!show)}>+ Pengguna</button></div>
    {show&&<UserForm token={token} roles={roles} done={()=>{setShow(false);load()}} fail={fail}/>}
    {editingUser&&<UserRoleEditor token={token} user={editingUser} roles={roles} done={()=>{setEditingUser(null);load()}} fail={fail}/>}<div className="table-wrap"><table><thead><tr><th>Nama</th><th>Akun</th><th>Role</th><th>Level</th><th>Status</th><th/></tr></thead><tbody>{rows.map(row=><tr key={row.id}><td><b>{row.full_name}</b><small>{row.email}</small></td><td>{row.username}</td><td>{row.roles.join(', ')||'-'}</td><td>{row.access_level}</td><td><span className={`badge ${row.active?'':'danger'}`}>{row.active?'AKTIF':'NONAKTIF'}</span></td><td><button className="link" onClick={()=>setEditingUser(row)}>Ubah role</button><button className="link" onClick={()=>resetPassword(row)}>Reset password</button><button className="link" onClick={()=>toggle(row)}>{row.active?'Nonaktifkan':'Aktifkan'}</button></td></tr>)}</tbody></table></div>
  </section>
}

function UserForm({token,roles,done,fail}:{token:string;roles:RoleRow[];done:()=>void;fail:(v:string)=>void}) {
  const [form,setForm]=useState({full_name:'',username:'',email:'',password:'',access_level:10,role_ids:[] as string[]})
  async function submit(e:FormEvent){e.preventDefault();try{await api('/admin/users',token,{method:'POST',body:JSON.stringify(form)});done()}catch{fail('Pengguna gagal dibuat. Periksa username, email, dan panjang password.')}}
  return <form className="stack-form" onSubmit={submit}><div className="form-row"><input placeholder="Nama lengkap" value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})} required/><input placeholder="Username" value={form.username} onChange={e=>setForm({...form,username:e.target.value})} required/><input placeholder="Email (opsional)" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/><input type="password" placeholder="Password minimal 12 karakter" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} required/><button className="action">Simpan</button></div><div className="checks">{roles.map(role=><label key={role.id}><input type="checkbox" checked={form.role_ids.includes(role.id)} onChange={()=>setForm({...form,role_ids:form.role_ids.includes(role.id)?form.role_ids.filter(id=>id!==role.id):[...form.role_ids,role.id]})}/><span>{role.name}<small>{role.code}</small></span></label>)}</div></form>
}

function UserRoleEditor({token,user,roles,done,fail}:{token:string;user:UserRow;roles:RoleRow[];done:()=>void;fail:(v:string)=>void}){const [selected,setSelected]=useState(roles.filter(role=>user.roles.includes(role.code)).map(role=>role.id));async function submit(e:FormEvent){e.preventDefault();try{await api(`/admin/users/${user.id}/roles`,token,{method:'PUT',body:JSON.stringify({role_ids:selected})});done()}catch{fail('Role pengguna gagal diperbarui.')}}return <form className="stack-form" onSubmit={submit}><div className="panel-title"><h2>Role {user.full_name}</h2><button className="action">Simpan Role</button></div><div className="checks">{roles.map(role=><label key={role.id}><input type="checkbox" checked={selected.includes(role.id)} onChange={()=>setSelected(selected.includes(role.id)?selected.filter(id=>id!==role.id):[...selected,role.id])}/><span>{role.name}<small>{role.code}</small></span></label>)}</div></form>}

function RolesPage({token,fail}:{token:string;fail:(value:string)=>void}) {
  const [roles,setRoles]=useState<RoleRow[]>([]);const [permissions,setPermissions]=useState<PermissionRow[]>([]);const [users,setUsers]=useState<UserRow[]>([]);const [units,setUnits]=useState<UnitRow[]>([]);const [assignments,setAssignments]=useState<AssignmentRow[]>([]);const [show,setShow]=useState(false);const [showAssignment,setShowAssignment]=useState(false);const [showUnit,setShowUnit]=useState(false);const [editingRole,setEditingRole]=useState<RoleRow|null>(null)
  const load=()=>Promise.all([api<RoleRow[]>('/admin/roles',token),api<PermissionRow[]>('/admin/permissions',token),api<UserRow[]>('/admin/users',token),api<UnitRow[]>('/admin/units',token),api<AssignmentRow[]>('/admin/role-assignments',token)]).then(([r,p,u,n,a])=>{setRoles(r);setPermissions(p);setUsers(u);setUnits(n);setAssignments(a)}).catch(()=>fail('Role, permission, dan pejabat aktif tidak dapat dimuat.'))
  useEffect(()=>{load()},[token])
  async function toggleAssignment(row:AssignmentRow){try{await api(`/admin/role-assignments/${row.id}?active=${!row.active}`,token,{method:'PATCH'});await load()}catch{fail('Status pejabat aktif gagal diubah.')}}
  return <section className="panel"><div className="panel-title"><h2>Role & permission</h2><div><button className="link" onClick={()=>setShowUnit(!showUnit)}>+ Unit / AKD</button><button className="link" onClick={()=>setShowAssignment(!showAssignment)}>+ Pejabat aktif</button><button className="action" onClick={()=>setShow(!show)}>+ Role</button></div></div>{showUnit&&<UnitForm token={token} units={units} done={()=>{setShowUnit(false);load()}} fail={fail}/>} {show&&<RoleForm token={token} permissions={permissions} done={()=>{setShow(false);load()}} fail={fail}/>} {editingRole&&<RolePermissionEditor token={token} role={editingRole} permissions={permissions} done={()=>{setEditingRole(null);load()}} fail={fail}/>} {showAssignment&&<AssignmentForm token={token} roles={roles} users={users} units={units} done={()=>{setShowAssignment(false);load()}} fail={fail}/>}<div className="cards">{roles.map(role=><article className="role-card" key={role.id}><div><b>{role.name}</b><span className="badge">{role.code}</span></div><small>{role.permissions.length} permission</small><p>{role.permissions.map(p=>p.code).join(' · ')||'Belum ada permission'}</p><button className="link" onClick={()=>setEditingRole(role)}>Ubah permission</button></article>)}</div><h2 className="section-title">Pejabat / role assignment aktif</h2><table><thead><tr><th>Role</th><th>Nama</th><th>Mulai</th><th>Selesai</th><th>Status</th><th/></tr></thead><tbody>{assignments.map(a=><tr key={a.id}><td>{a.role_code}</td><td>{a.user_name}</td><td>{a.valid_from}</td><td>{a.valid_until??'-'}</td><td><span className="badge">{a.active?'AKTIF':'NONAKTIF'}</span></td><td><button className="link" onClick={()=>toggleAssignment(a)}>{a.active?'Nonaktifkan':'Aktifkan'}</button></td></tr>)}</tbody></table></section>
}

function UnitForm({token,units,done,fail}:{token:string;units:UnitRow[];done:()=>void;fail:(v:string)=>void}){const [code,setCode]=useState('');const [name,setName]=useState('');const [parentId,setParentId]=useState('');async function submit(e:FormEvent){e.preventDefault();try{await api('/admin/units',token,{method:'POST',body:JSON.stringify({code:code.toUpperCase(),name,parent_id:parentId||null})});done()}catch{fail('Unit / AKD gagal dibuat. Pastikan kode unik.')}}return <form className="inline-form" onSubmit={submit}><input value={code} onChange={e=>setCode(e.target.value)} placeholder="Kode unit" required/><input value={name} onChange={e=>setName(e.target.value)} placeholder="Nama unit / AKD" required/><select value={parentId} onChange={e=>setParentId(e.target.value)}><option value="">Tanpa induk</option>{units.map(unit=><option key={unit.id} value={unit.id}>{unit.name}</option>)}</select><button className="action">Simpan Unit</button></form>}

function AssignmentForm({token,roles,users,units,done,fail}:{token:string;roles:RoleRow[];users:UserRow[];units:UnitRow[];done:()=>void;fail:(v:string)=>void}){const [roleId,setRoleId]=useState('');const [userId,setUserId]=useState('');const [unitId,setUnitId]=useState('');const [validFrom,setValidFrom]=useState(new Date().toISOString().slice(0,10));async function submit(e:FormEvent){e.preventDefault();try{await api('/admin/role-assignments',token,{method:'POST',body:JSON.stringify({role_id:roleId,user_id:userId,unit_id:unitId||null,valid_from:validFrom,metadata:{}})});done()}catch{fail('Pejabat aktif gagal disimpan. Pastikan role dan pengguna dipilih.')}}return <form className="inline-form" onSubmit={submit}><select value={roleId} onChange={e=>setRoleId(e.target.value)} required><option value="">Pilih role</option>{roles.map(r=><option key={r.id} value={r.id}>{r.code} — {r.name}</option>)}</select><select value={userId} onChange={e=>setUserId(e.target.value)} required><option value="">Pilih pengguna</option>{users.filter(u=>u.active).map(u=><option key={u.id} value={u.id}>{u.full_name}</option>)}</select><select value={unitId} onChange={e=>setUnitId(e.target.value)}><option value="">Semua unit</option>{units.map(u=><option key={u.id} value={u.id}>{u.name}</option>)}</select><input type="date" value={validFrom} onChange={e=>setValidFrom(e.target.value)}/><button className="action">Simpan Assignment</button></form>}

function RoleForm({token,permissions,done,fail}:{token:string;permissions:PermissionRow[];done:()=>void;fail:(v:string)=>void}){
  const [code,setCode]=useState('');const [name,setName]=useState('');const [selected,setSelected]=useState<string[]>([])
  async function submit(e:FormEvent){e.preventDefault();try{await api('/admin/roles',token,{method:'POST',body:JSON.stringify({code,name,permission_ids:selected})});done()}catch{fail('Role gagal dibuat. Gunakan kode huruf besar yang unik.')}}
  return <form className="stack-form" onSubmit={submit}><div className="form-row"><input placeholder="Kode, contoh VERIFIER" value={code} onChange={e=>setCode(e.target.value.toUpperCase())}/><input placeholder="Nama role" value={name} onChange={e=>setName(e.target.value)}/><button className="action">Simpan</button></div><div className="checks">{permissions.map(p=><label key={p.id}><input type="checkbox" checked={selected.includes(p.id)} onChange={()=>setSelected(selected.includes(p.id)?selected.filter(id=>id!==p.id):[...selected,p.id])}/><span>{p.code}<small>{p.description}</small></span></label>)}</div></form>
}

function RolePermissionEditor({token,role,permissions,done,fail}:{token:string;role:RoleRow;permissions:PermissionRow[];done:()=>void;fail:(v:string)=>void}){const [selected,setSelected]=useState(role.permissions.map(permission=>permission.id));async function submit(e:FormEvent){e.preventDefault();try{await api(`/admin/roles/${role.id}/permissions`,token,{method:'PUT',body:JSON.stringify({permission_ids:selected})});done()}catch{fail('Permission role gagal diperbarui.')}}return <form className="stack-form" onSubmit={submit}><div className="panel-title"><h2>Permission {role.name}</h2><button className="action">Simpan Permission</button></div><div className="checks">{permissions.map(permission=><label key={permission.id}><input type="checkbox" checked={selected.includes(permission.id)} onChange={()=>setSelected(selected.includes(permission.id)?selected.filter(id=>id!==permission.id):[...selected,permission.id])}/><span>{permission.code}<small>{permission.description}</small></span></label>)}</div></form>}

function WorkflowsPage({token,fail}:{token:string;fail:(value:string)=>void}){
  const [rows,setRows]=useState<WorkflowRow[]>([]);const [roles,setRoles]=useState<RoleRow[]>([]);const [show,setShow]=useState(false)
  const load=()=>Promise.all([api<WorkflowRow[]>('/admin/workflows',token),api<RoleRow[]>('/admin/roles',token)]).then(([workflows,roleRows])=>{setRows(workflows);setRoles(roleRows)}).catch(()=>fail('Workflow tidak dapat dimuat.'))
  useEffect(()=>{load()},[token]);async function publish(id:string){try{await api(`/admin/workflows/${id}/publish`,token,{method:'POST'});load()}catch{fail('Workflow gagal dipublikasikan.')}}
  return <section className="panel"><div className="panel-title"><h2>Versi workflow</h2><button className="action" onClick={()=>setShow(!show)}>+ Workflow</button></div>{show&&<WorkflowForm token={token} roles={roles} done={()=>{setShow(false);load()}} fail={fail}/>}<table><thead><tr><th>Workflow</th><th>Dokumen</th><th>Versi</th><th>Langkah</th><th>Status</th><th/></tr></thead><tbody>{rows.map(row=><tr key={row.id}><td><b>{row.name}</b></td><td>{row.document_type}</td><td>v{row.version}</td><td>{row.step_count}</td><td><span className="badge">{row.state}</span></td><td>{row.state==='DRAFT'&&<button className="link" onClick={()=>publish(row.id)}>Publikasikan</button>}</td></tr>)}</tbody></table></section>
}

function WorkflowForm({token,roles,done,fail}:{token:string;roles:RoleRow[];done:()=>void;fail:(v:string)=>void}){
  type StepDraft={name:string;role:string;actions:string;completion:string;returnStep:string};const empty=():StepDraft=>({name:'Pemeriksaan',role:roles[0]?.code??'',actions:'VERIFY,RETURN',completion:'ALL',returnStep:''});const [name,setName]=useState('');const [type,setType]=useState('MEETING_REQUEST');const [steps,setSteps]=useState<StepDraft[]>([empty()])
  function patch(index:number,value:Partial<StepDraft>){setSteps(steps.map((step,i)=>i===index?{...step,...value}:step))}
  async function submit(e:FormEvent){e.preventDefault();const body={name,document_type:type,steps:steps.map(step=>({step_key:step.name.trim().toUpperCase().replaceAll(' ','_'),name:step.name,assignment_rule:{role_code:step.role},allowed_actions:step.actions.split(',').map(value=>value.trim().toUpperCase()).filter(Boolean),completion_rule:step.completion,return_step_key:step.returnStep||null,note_required_on_return:true}))};try{await api('/admin/workflows',token,{method:'POST',body:JSON.stringify(body)});done()}catch{fail('Workflow gagal dibuat. Periksa role, action, nama langkah unik, dan tujuan RETURN.')}}
  return <form className="stack-form" onSubmit={submit}><div className="form-row"><input placeholder="Nama workflow" value={name} onChange={e=>setName(e.target.value)} required/><select value={type} onChange={e=>setType(e.target.value)}><option>MEETING_REQUEST</option><option>TRAVEL_REQUEST</option><option>INCOMING_CHAIRMAN</option><option>INCOMING_SECRETARY</option></select></div>{steps.map((step,index)=><div className="workflow-step" key={index}><b>Langkah {index+1}</b><input placeholder="Nama langkah" value={step.name} onChange={e=>patch(index,{name:e.target.value})} required/><select value={step.role} onChange={e=>patch(index,{role:e.target.value})} required><option value="">Pilih role</option>{roles.map(role=><option key={role.id} value={role.code}>{role.code} — {role.name}</option>)}</select><input placeholder="Action dipisahkan koma" value={step.actions} onChange={e=>patch(index,{actions:e.target.value})} required/><select value={step.completion} onChange={e=>patch(index,{completion:e.target.value})}><option>ALL</option><option>ANY</option><option>SELECTED</option></select><select value={step.returnStep} onChange={e=>patch(index,{returnStep:e.target.value})}><option value="">Tidak ada tujuan RETURN</option>{steps.filter((_,i)=>i!==index).map(other=><option key={other.name} value={other.name.trim().toUpperCase().replaceAll(' ','_')}>{other.name}</option>)}</select>{steps.length>1&&<button type="button" className="link" onClick={()=>setSteps(steps.filter((_,i)=>i!==index))}>Hapus</button>}</div>)}<div className="form-row"><button type="button" className="link" onClick={()=>setSteps([...steps,empty()])}>+ Tambah Langkah</button><button className="action">Simpan Draft</button></div></form>
}

function TemplatesPage({token,fail}:{token:string;fail:(value:string)=>void}){
  const [rows,setRows]=useState<TemplateRow[]>([]);const [code,setCode]=useState('MEETING_REQUEST_DPRD');const [name,setName]=useState('Permintaan Rapat DPRD');const [file,setFile]=useState<File|null>(null);const [busy,setBusy]=useState(false)
  const load=()=>api<TemplateRow[]>('/admin/templates',token).then(data=>{setRows(data);if(data.length&& !data.some(row=>row.code===code)){setCode(data[0].code);setName(data[0].name)}}).catch(()=>fail('Daftar template tidak dapat dimuat.'))
  useEffect(()=>{load()},[token])
  async function upload(e:FormEvent){e.preventDefault();if(!file)return fail('Pilih berkas DOCX terlebih dahulu.');const data=new FormData();data.append('code',code);data.append('name',name);data.append('upload',file);setBusy(true);try{const response=await fetch(`${API_BASE_URL}/admin/templates/upload`,{method:'POST',headers:{Authorization:`Bearer ${token}`},body:data});if(!response.ok)throw new Error(await response.text());setFile(null);await load()}catch{fail('Upload template gagal. Pastikan kode dikenali dan berkas DOCX valid.')}finally{setBusy(false)}}
  async function activate(id:string){try{await api(`/admin/templates/versions/${id}/activate`,token,{method:'POST'});await load()}catch{fail('Versi template gagal diaktifkan.')}}
  return <section className="panel"><div className="panel-title"><h2>Template dokumen resmi</h2></div><form className="inline-form" onSubmit={upload}><select value={code} onChange={e=>{setCode(e.target.value);const selected=rows.find(row=>row.code===e.target.value);if(selected)setName(selected.name)}}>{rows.map(row=><option key={row.id} value={row.code}>{row.name}</option>)}</select><input value={name} onChange={e=>setName(e.target.value)} placeholder="Nama template"/><input type="file" accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={e=>setFile(e.target.files?.[0]??null)}/><button className="action" disabled={busy}>{busy?'Mengunggah…':'Upload versi baru'}</button></form><div className="cards">{rows.map(row=><article className="role-card" key={row.id}><div><b>{row.name}</b><span className="badge">{row.versions.find(v=>v.active)?`v${row.versions.find(v=>v.active)?.version}`:'TIDAK AKTIF'}</span></div><p>Kode: {row.code}</p>{row.versions.map(version=><div className="template-version" key={version.id}><span>v{version.version} · {version.sha256_hash.slice(0,12)}…</span>{version.active?<span className="badge">AKTIF</span>:<button className="link" onClick={()=>activate(version.id)}>Aktifkan</button>}</div>)}</article>)}</div></section>
}

function AuditPage({token,fail}:{token:string;fail:(value:string)=>void}){const [rows,setRows]=useState<AuditRow[]>([]);useEffect(()=>{api<AuditRow[]>('/admin/audit-logs',token).then(setRows).catch(()=>fail('Audit log tidak dapat dimuat.'))},[token]);return <section className="panel"><h2>Audit log append-only</h2><table><thead><tr><th>Waktu</th><th>Aksi</th><th>Entitas</th><th>ID</th></tr></thead><tbody>{rows.map(r=><tr key={r.id}><td>{new Date(r.occurred_at).toLocaleString('id-ID')}</td><td><span className="badge">{r.action}</span></td><td>{r.entity_type}</td><td><code>{r.entity_id?.slice(0,8)??'-'}</code></td></tr>)}</tbody></table></section>}

function Login({ onAuthenticated }: { onAuthenticated: (token: string) => void }) {
  const [username,setUsername]=useState('');const [password,setPassword]=useState('');const [loading,setLoading]=useState(false);const [error,setError]=useState('')
  async function submit(event:FormEvent){event.preventDefault();if(!username.trim()||!password)return setError('Nama pengguna dan kata sandi wajib diisi.');setLoading(true);setError('');const body=new URLSearchParams({username:username.trim(),password});try{const response=await fetch(`${API_BASE_URL}/auth/login`,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body});if(!response.ok)throw new Error();const data=await response.json() as {access_token:string};onAuthenticated(data.access_token)}catch{setError('Login gagal. Periksa akun administrator dan koneksi backend.')}finally{setLoading(false)}}
  return <div className="login-page"><form className="login-card" onSubmit={submit}><div className="brand login-brand"><span>SD</span><div>SmartDispo<small>DPRD Kota Bitung</small></div></div><h1>Panel Administrator</h1><p>Masuk menggunakan akun yang dibuat pada server.</p><label>Nama pengguna<input value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username"/></label><label>Kata sandi<input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password"/></label>{error&&<div className="alert">{error}</div>}<button className="primary" disabled={loading}>{loading?'Memeriksa…':'Masuk'}</button></form></div>
}

function Metric({value,label,tone}:{value:string;label:string;tone:string}){return <article className={`metric ${tone}`}><strong>{value}</strong><span>{label}</span></article>}
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>)
