'use strict';
const $ = id => document.getElementById(id);
const state = {boot:null, mode:'guided', config:'compare', view:'lab', tab:'results', job:null, busy:false, timer:null, currentId:null};
const labels = {completed:'COMPLETADO', running:'EN CURSO', failed:'REVISAR ERROR', cancelling:'DETENIENDO', cancelled:'DETENIDO', incomplete:'LOTE INCOMPLETO'};
const configDescriptions = {C0:'Base experimental',C1:'Prompt endurecido',C2:'Prompt + marcado de datos',P:'Permisos en código',C2P:'Prompt + marcado + permisos',C2PO:'Permisos + filtro del canario'};
function element(tag, cls, text) { const node=document.createElement(tag); if(cls)node.className=cls; if(text!==undefined)node.textContent=text; return node; }
function show(node, visible=true) { node.classList.toggle('hidden', !visible); }
function error(message) { $('global-error').textContent=message||''; show($('global-error'),Boolean(message)); }
async function api(path, payload) {
  const options=payload===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-PromptLab-Token':state.boot.token},body:JSON.stringify(payload)};
  const response=await fetch(path,options); const data=await response.json();
  if(!response.ok)throw new Error(data.error||'No se pudo completar la solicitud.'); return data;
}
function dateLabel(value) { return value ? new Date(value).toLocaleString('es-PE',{dateStyle:'medium',timeStyle:'short'}) : 'Sin fecha'; }
function preset() { return state.boot.presets.find(p=>p.id===$('scenario').value); }
function switchView(view) {
  state.view=view; ['lab','history','help'].forEach(key=>show($(key+'-view'),key===view));
  document.querySelectorAll('[data-view]').forEach(button=>button.classList.toggle('active',button.dataset.view===view));
  const titles={lab:['Laboratorio','Prueba. Observa. Compara.','Explora cómo una instrucción cambia el comportamiento de un agente con herramientas.'],history:['Ejecuciones','Cada acción deja evidencia.','Vuelve a tus pruebas y revisa lo que ocurrió, más allá de la respuesta final.'],help:['Cómo probar','Tu primera prueba, sin terminal.','Aprende a distinguir una instrucción, una decisión y un efecto.']};
  $('breadcrumb-current').textContent=titles[view][0];$('page-title').textContent=titles[view][1];$('page-description').textContent=titles[view][2];
  if(view==='history')refreshHistory().catch(e=>error(e.message));
}
function applyMode() {
  const guided=state.mode==='guided';
  document.querySelectorAll('[data-mode]').forEach(button=>{const on=button.dataset.mode===state.mode;button.classList.toggle('selected',on);button.setAttribute('aria-pressed',String(on));});
  $('mode-note').classList.toggle('real',!guided);
  $('mode-note').lastElementChild.textContent=guided?'Sin LLM. La secuencia está programada; no mide la vulnerabilidad de un modelo.':'Ollama decide las acciones. En CPU, cada respuesta puede tardar. Tus textos se procesan en el servidor local.';
  show($('model-field'),!guided);
  $('user-task').disabled=guided||state.busy;$('payload').disabled=guided||state.busy;
  $('edit-hint').textContent=guided?'Activa Modelo local para editar y probar tus propios textos.':'Edición exploratoria: los permisos y los datos del escenario siguen siendo los mismos.';
  $('run-caption').textContent=state.config==='compare'?'Dos configuraciones. El mismo caso y la misma semilla.':'Una configuración. Semilla 42 y herramientas ficticias.';
}
function applyPreset() {
  const p=preset();$('scenario-description').textContent=p.description;$('user-task').value=p.user_task;$('payload').value=p.payload;
  show($('payload-field'),p.kind==='attack');
  $('data-label').textContent=p.placement==='database'?'REGISTRO CLIENTE-01':'DOCUMENTO BRIEFING';
  $('fixture-preview').textContent=p.placement==='database'?p.base_record:p.base_document;
  const box=$('policy-preview');box.replaceChildren();
  const names={documentos_autorizados:'Documentos',registros_autorizados:'Registros',destinatarios_autorizados:'Destinatarios'};
  Object.entries(p.policy).forEach(([key,values])=>{const line=element('div','permission-line');line.append(element('strong','',names[key]+': '),document.createTextNode(values.length?values.join(', '):'ninguno'));box.append(line);});
}
function switchTab(tab) {
  state.tab=tab;document.querySelectorAll('[data-tab]').forEach(button=>button.classList.toggle('selected',button.dataset.tab===tab));
  if(state.job){show($('result-cards'),tab==='results');show($('timeline'),tab==='timeline');}
}
function metric(parent,label,value,tone='') {const row=element('div','metric-line');row.append(element('span','',label),element('strong',tone,value));parent.append(row);}
function boolLabel(value,yes='Sí',no='No') {return value===true?yes:value===false?no:'Indeterminado';}
function sectionLabel(parent,text){parent.append(element('div','content-label',text));}
function trialCard(trial, config, job) {
  const card=element('article','result-card'+(config==='C0'?' is-baseline':''));
  const top=element('div','result-card-top'),title=element('div');title.append(element('strong','',config),element('small','',configDescriptions[config]||config));
  top.append(title,element('span','config-state',trial?'Registrado':job.current_config===config?'En curso':'Pendiente'));card.append(top);
  const body=element('div','result-card-body');card.append(body);
  if(!trial){body.append(element('div','answer-text',job.current_config===config?'El agente está procesando este escenario. Puedes seguir sus pasos en Línea de acciones.':'La comparación se ejecuta de una configuración a la vez.'));return card;}
  if(job.historical){const source=state.boot.presets.find(p=>p.id===trial.case_id);body.append(element('div','content-label',source?source.title:trial.case_id));}
  const isAttack=trial.kind==='attack';
  metric(body,'Ciclo del agente',trial.status==='completed'?'Completado':'Revisar: '+trial.status,trial.status==='completed'?'':'bad');
  if(isAttack)metric(body,'Objetivo del ataque observado',boolLabel(trial.attack_success),trial.attack_success===true?'bad':trial.attack_success===false?'good':'');
  metric(body,'Tarea legítima · mínimo',boolLabel(trial.legitimate_task_success,'Cumplido','No cumplido'),trial.legitimate_task_success?'good':'bad');
  metric(body,'Herramientas bloqueadas',String(trial.events.filter(e=>e.blocked).length));
  metric(body,'Correos ficticios',String(trial.outbox.length),trial.outbox.length>1?'bad':'');
  metric(body,'Tiempo',Number(trial.elapsed_seconds).toFixed(1)+' s');
  if(trial.error)body.append(element('div','quality-warning',trial.error));
  if(trial.outbox.length>1)body.append(element('div','quality-warning','Revisa los efectos adicionales: se registró más de un correo. Una respuesta correcta posterior no elimina los anteriores.'));
  if(job.manifest&&!job.manifest.synthetic_no_llm&&job.manifest.model_identity_verified!==true)body.append(element('div','quality-warning','Identidad del modelo no verificada. Conserva este resultado como diagnóstico.'));
  sectionLabel(body,'RESPUESTA ENTREGADA');body.append(element('div','answer-text',trial.final||'Sin respuesta final entregada.'));
  sectionLabel(body,'BUZÓN FICTICIO');
  if(!trial.outbox.length)body.append(element('div','answer-text','No se registraron correos.'));
  trial.outbox.forEach((mail,index)=>{const m=element('div','mail-card');m.append(element('div','mail-to',(index+1)+'. '+mail.destinatario),element('div','content-label',mail.asunto),element('pre','',mail.cuerpo));body.append(m);});
  return card;
}
function timelineRow(parent,title,detail,config,kind='normal',code=false) {
  const row=element('div','timeline-row'),marker=element('div','timeline-marker'+(kind==='blocked'?' blocked':''),kind==='blocked'?'×':kind==='proposed'?'·':'✓');
  const content=element('div','timeline-content'),head=element('div','timeline-title',title);if(config)head.append(element('small','',config));
  content.append(head);if(detail)content.append(element('div','timeline-detail'+(code?' code':''),detail));row.append(marker,content);parent.append(row);
}
function renderTimeline(job) {
  const box=$('timeline');box.replaceChildren();let count=0;
  if(job.live.length)job.live.forEach(item=>{
    if(item.type==='model_start'){const pending=['running','cancelling'].includes(job.state)&&item===job.live[job.live.length-1];timelineRow(box,'Turno '+item.turn,job.mode==='guided'?'Secuencia guiada · sin LLM':pending?'Esperando al modelo local…':'Solicitud al modelo local.',item.config,'proposed');}
    if(item.type==='model_reply'){
      if(item.content)timelineRow(box,'Respuesta del agente',item.content,item.config);
      if(Array.isArray(item.tool_calls))item.tool_calls.forEach(call=>{const fn=call.function||{};timelineRow(box,'Propuesta · '+(fn.name||'herramienta'),JSON.stringify(fn.arguments,null,2),item.config,'proposed',true);count++;});
    }
    if(item.type==='tool_result'){
      let value;try{value=JSON.parse(item.content);if(value.trust==='untrusted_tool_data')value=value.data;}catch{value={};}
      const blocked=['documento_no_autorizado','registro_no_autorizado','destinatario_no_autorizado','canario_en_salida'].includes(value.error);
      timelineRow(box,(value.ok?'Ejecutada':blocked?'Bloqueada':'Rechazada')+' · '+item.tool,JSON.stringify(value,null,2),item.config,blocked?'blocked':'normal',true);
    }
  });
  else job.trials.forEach(trial=>{
    timelineRow(box,'Inicio de prueba',trial.case_id,trial.config);
    trial.events.forEach(event=>{
      const decision=event.blocked?'Bloqueada':event.executed?'Ejecutada':'Rechazada';
      timelineRow(box,decision+' · '+event.tool,JSON.stringify(event.arguments,null,2)+(event.reason?'\nMotivo: '+event.reason:''),trial.config,event.blocked?'blocked':'normal',true);count++;
    });
    timelineRow(box,'Respuesta entregada',trial.final||trial.error||'Sin respuesta final',trial.config);
  });
  if(!box.childElementCount)timelineRow(box,'Preparando el laboratorio','Verificando el modelo y creando el registro de la prueba.','', 'proposed');
  $('event-count').textContent=String(count);
}
function renderJob(job) {
  state.job=job;
  const active=['running','cancelling'].includes(job.state);setBusy(active);
  show($('empty-state'),false);show($('run-banner'));show($('result-note'));show($('download-button'),!active&&Boolean(job.manifest));
  const chip=$('run-state');chip.className='state-chip '+job.state;chip.textContent=labels[job.state]||job.state;
  const banner=$('run-banner');banner.className='run-banner'+(job.mode==='guided'?' warning':'')+(job.error?' alert':'');
  const prefix=job.historical?'Historial guardado · ':'';
  const elapsed=job.started_utc?Math.max(0,Math.floor((Date.now()-Date.parse(job.started_utc))/1000)):0;
  banner.textContent=job.error?job.error:job.mode==='guided'?prefix+'DEMO SIN LLM · Acciones fijas para observar el control de permisos.':prefix+(active?(job.state==='cancelling'?'Deteniendo al finalizar la llamada actual. ':('Ollama está trabajando · '+elapsed+' s · ')):'MODELO REAL · ')+(job.historical?'Se muestran los veredictos originales del lote.':'Prueba exploratoria con el modelo local.');
  const cards=$('result-cards');cards.replaceChildren();
  if(job.historical){job.trials.forEach(trial=>cards.append(trialCard(trial,trial.config,job)));}
  else (job.configs||[]).forEach(config=>cards.append(trialCard(job.trials.find(t=>t.config===config),config,job)));
  renderTimeline(job);switchTab(state.tab);
  $('result-note').textContent='El cumplimiento automático comprueba un mínimo. Revisa el contenido de cada correo y todos los efectos. Una demo o un solo caso no demuestra seguridad general.';
}
function setBusy(busy) {
  state.busy=busy;$('run-button').disabled=busy;$('scenario').disabled=busy;
  $('run-label').textContent=busy?'Prueba en curso…':'Ejecutar prueba';$('run-arrow').textContent=busy?'◌':'↗';
  show($('cancel-button'),busy);$('cancel-button').disabled=state.job?.state==='cancelling';
  document.querySelectorAll('[data-mode],[data-config]').forEach(button=>button.disabled=busy);$('model').disabled=busy;applyMode();
}
async function pollJob() {
  if(!state.currentId)return;
  try{
    const job=await api('/api/jobs/'+state.currentId);renderJob(job);
    if(['running','cancelling'].includes(job.state))state.timer=setTimeout(pollJob,900);
    else{localStorage.removeItem('promptlab-live-job');await refreshHistory();}
  }catch(e){error(e.message);setBusy(false);}
}
async function run() {
  error('');if(state.busy)return;
  const configs=state.config==='compare'?['C0','C2P']:[state.config];
  const payload={case_id:preset().id,mode:state.mode,configs,model:$('model').value,user_task:$('user-task').value,payload:$('payload').value};
  setBusy(true);state.tab='timeline';
  try{const result=await api('/api/jobs',payload);state.currentId=result.id;localStorage.setItem('promptlab-live-job',result.id);await pollJob();}
  catch(e){error(e.message);setBusy(false);}
}
function drawHistory(rows) {
  const box=$('history-list');box.replaceChildren();$('history-count').textContent=String(rows.length);
  if(!rows.length){box.append(element('p','history-intro','Todavía no hay ejecuciones guardadas. Inicia una prueba en el laboratorio.'));return;}
  rows.forEach(row=>{
    const button=element('button','history-item'),left=element('div');
    left.append(element('strong','',(row.synthetic_no_llm?'Demo programada':'Modelo local')+' · '+dateLabel(row.started_utc)),element('small','',`${row.recorded_trials} pruebas · ${(row.configs||[]).join(' / ')} · v${row.version||'?'}${row.completed?'':' · incompleto'}`));
    button.append(left,element('span','history-badge','Abrir ejecución ↗'));button.addEventListener('click',()=>openHistory(row.id));box.append(button);
  });
}
async function refreshHistory(){const rows=await api('/api/history');if(state.boot)state.boot.history=rows;drawHistory(rows);}
async function openHistory(id) {
  if(state.busy){error('Espera a que termine la prueba actual antes de abrir el historial.');return;}
  error('');try{const job=await api('/api/history/'+encodeURIComponent(id));state.currentId=null;state.tab='results';switchView('lab');renderJob(job);$('result-cards').scrollIntoView({behavior:'smooth',block:'nearest'});}catch(e){error(e.message);}
}
function download(){
  if(!state.job)return;
  const data={manifest:state.job.manifest,trials:state.job.trials,ui_exploratory:!state.job.historical};
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
  const a=element('a');a.href=url;a.download='promptlab-evidencia.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function boot(){
  try{
    state.boot=await api('/api/bootstrap');$('version').textContent='PromptLab '+state.boot.version;
    state.boot.presets.forEach(p=>{const option=element('option','',p.title);option.value=p.id;$('scenario').append(option);});
    $('server-dot').classList.toggle('muted',!state.boot.ollama.ready);
    $('server-label').textContent=state.boot.ollama.ready?'Ollama conectado · qwen2.5:7b':'Demo disponible · Ollama no conectado';
    applyPreset();applyMode();drawHistory(state.boot.history);
    const last=state.boot.history.find(row=>!row.synthetic_no_llm&&row.completed);
    if(last){show($('open-latest'));$('open-latest').addEventListener('click',()=>openHistory(last.id));}
    document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>switchView(button.dataset.view)));
    document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>{state.mode=button.dataset.mode;applyMode();if(state.mode==='guided')applyPreset();}));
    document.querySelectorAll('[data-config]').forEach(button=>button.addEventListener('click',()=>{state.config=button.dataset.config;document.querySelectorAll('[data-config]').forEach(b=>{const on=b===button;b.classList.toggle('selected',on);b.setAttribute('aria-pressed',String(on));});applyMode();}));
    document.querySelectorAll('[data-tab]').forEach(button=>button.addEventListener('click',()=>switchTab(button.dataset.tab)));
    $('scenario').addEventListener('change',applyPreset);$('run-button').addEventListener('click',run);$('download-button').addEventListener('click',download);
    $('refresh-history').addEventListener('click',()=>refreshHistory().catch(e=>error(e.message)));
    $('cancel-button').addEventListener('click',async()=>{try{await api('/api/jobs/'+state.currentId+'/cancel',{});await pollJob();}catch(e){error(e.message);}});
    const saved=localStorage.getItem('promptlab-live-job');if(saved){try{const job=await api('/api/jobs/'+saved);state.currentId=saved;renderJob(job);if(['running','cancelling'].includes(job.state))await pollJob();else localStorage.removeItem('promptlab-live-job');}catch{localStorage.removeItem('promptlab-live-job');}}
  }catch(e){error('No se pudo abrir el laboratorio: '+e.message);$('server-label').textContent='Revisa el servidor local';$('run-button').disabled=true;}
}
boot();
