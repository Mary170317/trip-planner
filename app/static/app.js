"use strict";
const $ = (s) => document.querySelector(s);
const state = { user:null, mode:"login", offset:0, limit:12, trips:[], selected:null };
const money = (n) => Number(n || 0).toLocaleString("ru-RU", {minimumFractionDigits:2, maximumFractionDigits:2})+" ₽";
const escapeHtml = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const val = (s) => $(s).value;
let toastTimer;
function toast(message){ const el=$("#toast");el.textContent=message;el.classList.remove("hidden");clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.add("hidden"),4000); }
async function api(path, options={}){
 const response=await fetch(path,{credentials:"same-origin",...options,headers:{"Content-Type":"application/json",...(options.headers||{})}});
 if(response.status===204)return null;
 const body=await response.json().catch(()=>null);
 if(!response.ok){
  const detail=body?.detail;
  const msg=Array.isArray(detail)?detail.map(e=>e.msg).join("; "):typeof detail==="string"?detail:"Ошибка запроса";
  if(response.status===401 && !path.includes("/login") && !path.includes("/change-password")) showAuth();
  throw new Error(msg);
 }
 return body;
}
function showAuth(){state.user=null;$("#auth").classList.remove("hidden");$("#dashboard").classList.add("hidden");$("#userbar").classList.add("hidden");}
function showDashboard(user){state.user=user;$("#username").textContent=user.username;$("#userbar").classList.remove("hidden");$("#auth").classList.add("hidden");$("#dashboard").classList.remove("hidden");$("#admin-panel").classList.toggle("hidden",!user.is_admin);refresh();}
async function refresh(){await Promise.all([loadTrips(),loadStats()]);if(state.user?.is_admin)loadAdmin();}
async function loadTrips(){
 const params=new URLSearchParams({status:val("#status"),sort:val("#sort"),limit:String(state.limit),offset:String(state.offset)});
 if(val("#search").trim())params.set("q",val("#search").trim());
 const trips=await api("/api/trips?"+params);
 state.trips=trips;
 $("#trip-list").innerHTML=trips.length?trips.map(t=>`<article class="trip-card"><span class="pill ${t.is_completed?"done":""}">${t.is_completed?"✓ Завершена":"◷ В планах"}</span><h3>${escapeHtml(t.title)}</h3><p>${escapeHtml(t.description||"Добавьте описание путешествия")}</p><div class="meta">📅 ${escapeHtml(t.start_date)} — ${escapeHtml(t.end_date)}</div><div class="bottom"><strong>${money(t.budget)}</strong><button class="secondary" data-open="${t.id}">Открыть →</button></div></article>`).join(""):'<div class="empty">✈️ Пока нет поездок. Создайте первую!</div>';
 $("#page-info").textContent="Страница "+(Math.floor(state.offset/state.limit)+1);
 $("#prev").disabled=state.offset===0;$("#next").disabled=trips.length<state.limit;
}
async function loadStats(){
 const data=await api("/api/trips/stats");
 $("#stat-count").textContent=data.total_trips;$("#stat-budget").textContent=money(data.total_budget);$("#stat-avg").textContent=money(data.avg_budget);
 $("#month-stats").innerHTML=data.by_month.length?data.by_month.map(m=>`<div class="month-row"><span>${escapeHtml(m.month)} · ${m.trips_count} поездок</span><strong>${money(m.total_budget)}</strong></div>`).join(""):'<p class="muted">Статистика появится после добавления поездок.</p>';
}
async function loadAdmin(){
 try{
 const [users,trips]=await Promise.all([api("/api/admin/users"),api("/api/admin/trips")]);
 $("#admin-content").textContent=`Пользователей: ${users.length} · Всего поездок: ${trips.length}`;
 }catch(e){toast(e.message);}
}
function openModal(title,content){$("#modal-title").textContent=title;$("#modal-content").innerHTML=content;$("#modal").classList.remove("hidden");}
function closeModal(){$("#modal").classList.add("hidden");state.selected=null;}
const tripForm=(t={})=>`<form id="trip-form" class="form-grid">
<label class="full">Название<input name="title" maxlength="200" required value="${escapeHtml(t.title||"")}" placeholder="Например, выходные в Казани"></label>
<label class="full">Описание<textarea name="description" placeholder="Куда едем и что хотим увидеть">${escapeHtml(t.description||"")}</textarea></label>
<label>Дата начала<input type="date" name="start_date" required value="${escapeHtml(t.start_date||"")}"></label>
<label>Дата окончания<input type="date" name="end_date" required value="${escapeHtml(t.end_date||"")}"></label>
<label>Бюджет, ₽<input type="number" min="0" max="99999999" step=".01" name="budget" required value="${escapeHtml(t.budget??"0")}"></label>
<label>Статус<select name="is_completed"><option value="false" ${!t.is_completed?"selected":""}>В планах</option><option value="true" ${t.is_completed?"selected":""}>Завершена</option></select></label>
<div class="full actions"><button class="primary">💾 Сохранить</button><button type="button" class="secondary" id="cancel-form">Отмена</button></div></form>`;
function editTrip(t=null){
 openModal(t?"Редактировать поездку":"Новая поездка",tripForm(t||{}));
 $("#cancel-form").onclick=closeModal;
 $("#trip-form").onsubmit=async(e)=>{
  e.preventDefault();const d=Object.fromEntries(new FormData(e.target));d.is_completed=d.is_completed==="true";
  try{await api(t?"/api/trips/"+t.id:"/api/trips",{method:t?"PATCH":"POST",body:JSON.stringify(d)});closeModal();state.offset=0;await refresh();toast("Поездка сохранена");}catch(err){toast(err.message);}
 };
}
async function openTrip(id){
 try{
  const [trip,items]=await Promise.all([api("/api/trips/"+id),api("/api/trips/"+id+"/plan-items")]);
  state.selected=trip;
  const rows=items.map(i=>`<div class="item"><div><strong>${i.is_done?"✓ ":""}${escapeHtml(i.title)}</strong><br><small>${escapeHtml(i.day_date)} · ${escapeHtml(i.time_text||"Время не указано")} · ${escapeHtml(i.place||"Место не указано")} · ${money(i.estimated_cost)}</small></div><div class="actions"><button class="secondary" data-item-edit="${i.id}">✎</button><button class="secondary danger" data-item-delete="${i.id}">✕</button></div></div>`).join("");
  openModal(trip.title,`<p class="muted">${escapeHtml(trip.description||"Без описания")}</p><p>📅 ${escapeHtml(trip.start_date)} — ${escapeHtml(trip.end_date)}<br>💰 ${money(trip.budget)}</p><div class="actions"><button id="edit-trip" class="secondary">Редактировать</button><button id="delete-trip" class="secondary danger">Удалить поездку</button></div><hr><h2>План по дням</h2><div id="items-list">${rows||'<p class="muted">Пунктов пока нет.</p>'}</div><button id="new-item" class="primary" style="margin-top:20px">＋ Добавить пункт</button>`);
  $("#edit-trip").onclick=()=>editTrip(trip);
  $("#delete-trip").onclick=async()=>{if(!confirm("Удалить поездку вместе со всеми пунктами плана?"))return;try{await api("/api/trips/"+id,{method:"DELETE"});closeModal();await refresh();toast("Поездка удалена");}catch(e){toast(e.message);}};
  $("#new-item").onclick=()=>editItem(trip);
  $("#items-list").onclick=async e=>{
   const edit=e.target.closest("[data-item-edit]"),del=e.target.closest("[data-item-delete]");
   if(edit){editItem(trip,items.find(i=>i.id===Number(edit.dataset.itemEdit)));}
   if(del && confirm("Удалить пункт плана?")){try{await api("/api/plan-items/"+del.dataset.itemDelete,{method:"DELETE"});await openTrip(id);}catch(err){toast(err.message);}}
  };
 }catch(e){toast(e.message);}
}
function editItem(trip,item=null){
 const html=`<form id="item-form" class="form-grid">
<label class="full">Название<input name="title" required maxlength="200" value="${escapeHtml(item?.title||"")}" placeholder="Например, прогулка по центру"></label>
<label>Дата<input type="date" name="day_date" min="${trip.start_date}" max="${trip.end_date}" required value="${item?.day_date||trip.start_date}"></label>
<label>Время<input name="time_text" type="time" value="${escapeHtml(item?.time_text||"")}"></label>
<label class="full">Место<input name="place" maxlength="200" value="${escapeHtml(item?.place||"")}" placeholder="Адрес или название места"></label>
<label>Стоимость, ₽<input type="number" name="estimated_cost" min="0" max="99999999" step=".01" required value="${item?.estimated_cost??0}"></label>
<label>Выполнение<select name="is_done"><option value="false" ${!item?.is_done?"selected":""}>Не выполнено</option><option value="true" ${item?.is_done?"selected":""}>Выполнено</option></select></label>
<div class="full actions"><button class="primary">Сохранить</button><button type="button" class="secondary" id="back-to-trip">Назад</button></div></form>`;
 openModal(item?"Изменить пункт":"Новый пункт плана",html);
 $("#back-to-trip").onclick=()=>openTrip(trip.id);
 $("#item-form").onsubmit=async e=>{
  e.preventDefault();const data=Object.fromEntries(new FormData(e.target));data.is_done=data.is_done==="true";data.time_text=data.time_text||null;data.place=data.place||null;
  try{await api(item?"/api/plan-items/"+item.id:"/api/trips/"+trip.id+"/plan-items",{method:item?"PATCH":"POST",body:JSON.stringify(data)});await openTrip(trip.id);toast("Пункт сохранён");}catch(err){toast(err.message);}
 };
}
document.addEventListener("DOMContentLoaded",async()=>{
 try{showDashboard(await api("/api/auth/me"));}catch{showAuth();}
 document.querySelectorAll(".tab").forEach(b=>b.onclick=()=>{state.mode=b.dataset.mode;document.querySelectorAll(".tab").forEach(x=>x.classList.toggle("active",x===b));$("#auth-submit").textContent=state.mode==="login"?"Войти →":"Создать аккаунт →";});
 $("#auth-form").onsubmit=async e=>{e.preventDefault();try{const user=await api("/api/auth/"+state.mode,{method:"POST",body:JSON.stringify({username:val("#auth-user"),password:val("#auth-password")})});$("#auth-form").reset();showDashboard(user);}catch(err){toast(err.message);}};
 $("#logout").onclick=async()=>{try{await api("/api/auth/logout",{method:"POST"});showAuth();}catch(err){toast(err.message);}};
 $("#new-trip").onclick=()=>editTrip();
 $("#trip-list").onclick=e=>{const b=e.target.closest("[data-open]");if(b)openTrip(Number(b.dataset.open));};
 let searchTimer;$("#search").oninput=()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{state.offset=0;loadTrips().catch(e=>toast(e.message));},250);};
 for(const id of ["#status","#sort"])$(id).onchange=()=>{state.offset=0;loadTrips().catch(e=>toast(e.message));};
 $("#prev").onclick=()=>{state.offset=Math.max(0,state.offset-state.limit);loadTrips().catch(e=>toast(e.message));};
 $("#next").onclick=()=>{state.offset+=state.limit;loadTrips().catch(e=>toast(e.message));};
 $("#modal-close").onclick=closeModal;$("#modal").onclick=e=>{if(e.target.id==="modal")closeModal();};
 document.addEventListener("keydown",e=>{if(e.key==="Escape")closeModal();});
 $("#password-form").onsubmit=async e=>{e.preventDefault();try{const r=await api("/api/auth/change-password",{method:"POST",body:JSON.stringify({old_password:val("#old-password"),new_password:val("#new-password")})});$("#password-form").reset();toast(r.message);}catch(err){toast(err.message);}};
});
