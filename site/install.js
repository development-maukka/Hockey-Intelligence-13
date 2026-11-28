/* Installation UI is optional: blocked storage and unsupported browsers must not affect the dashboard. */
(()=>{
 const strings={
 fi:{install:'Asenna sovellus',message:'Lisää Hockey Intelligence 13 aloitusnäyttöön ja avaa se suoraan sovelluksena.',dismiss:'Sulje asennusehdotus',close:'Sulje',help:'Asennusohje',firefox:'Avaa Firefoxin ⋮-valikko ja valitse Asenna tai Lisää sovellus aloitusnäyttöön. Vahvista lisääminen.',ios:'Avaa sivu Safarissa. Valitse Jaa → Lisää Koti-valikkoon ja vahvista lisääminen.',mac:'Valitse Safarissa Jaa → Lisää Dockiin. Jos valintaa ei ole, avaa sivu Chromessa tai Edgessä ja käytä selaimen asennusvalintaa.',android:'Avaa selaimen ⋮-valikko ja valitse Asenna sovellus tai Lisää aloitusnäyttöön. Jos valintaa ei ole, kokeile Chromea tai Firefoxia.',desktop:'Käytä selaimen osoiterivin tai valikon asennusvalintaa. Jos valintaa ei ole, avaa sivu Chromessa tai Edgessä; Macilla voit käyttää myös Safarin Lisää Dockiin -toimintoa.',note:'Valikkojen nimet voivat vaihdella selaimen kielen ja version mukaan.'},
 de:{install:'App installieren',message:'Füge Hockey Intelligence 13 zum Startbildschirm hinzu und öffne es direkt als App.',dismiss:'Installationshinweis schliessen',close:'Schliessen',help:'Installationsanleitung',firefox:'Öffne das ⋮-Menü in Firefox und wähle Installieren oder App zum Startbildschirm hinzufügen. Bestätige das Hinzufügen.',ios:'Öffne die Seite in Safari. Wähle Teilen → Zum Home-Bildschirm und bestätige das Hinzufügen.',mac:'Wähle in Safari Teilen → Zum Dock hinzufügen. Falls die Option fehlt, öffne die Seite in Chrome oder Edge und nutze die Installationsoption des Browsers.',android:'Öffne das ⋮-Menü des Browsers und wähle App installieren oder Zum Startbildschirm hinzufügen. Falls die Option fehlt, versuche es mit Chrome oder Firefox.',desktop:'Nutze die Installationsoption in der Adressleiste oder im Browsermenü. Falls sie fehlt, öffne die Seite in Chrome oder Edge; auf dem Mac kannst du auch Zu Dock hinzufügen in Safari verwenden.',note:'Die Menünamen können je nach Sprache und Browserversion abweichen.'},
 en:{install:'Install app',message:'Add Hockey Intelligence 13 to your home screen and open it directly as an app.',dismiss:'Dismiss installation suggestion',close:'Close',help:'Installation instructions',firefox:'Open Firefox’s ⋮ menu and choose Install or Add app to Home screen. Confirm adding the app.',ios:'Open this page in Safari. Choose Share → Add to Home Screen and confirm adding the app.',mac:'In Safari, choose Share → Add to Dock. If the option is unavailable, open this page in Chrome or Edge and use the browser’s install option.',android:'Open your browser’s ⋮ menu and choose Install app or Add to Home screen. If unavailable, try Chrome or Firefox.',desktop:'Use the install option in your browser’s address bar or menu. If unavailable, open this page in Chrome or Edge; on a Mac you can also use Add to Dock in Safari.',note:'Menu names may vary with your browser’s language and version.'}
 };
 let pref='';try{pref=localStorage.getItem('hockey-language')}catch{}
 const language=['fi','de','en'].includes(pref)?pref:(navigator.language||'en').slice(0,2).toLowerCase(),t=strings[language]||strings.en;
 const ua=navigator.userAgent||'',ios=/iPad|iPhone|iPod/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1),android=/Android/.test(ua),safari=/Safari/.test(ua)&&!/Chrome|Chromium|Edg|OPR/.test(ua);
 const helpKey=ios?'ios':android&&/Firefox/.test(ua)?'firefox':android?'android':/Mac/.test(ua)&&safari?'mac':'desktop';
 const media=window.matchMedia('(display-mode: standalone)'),full=window.matchMedia('(display-mode: fullscreen)');
 let installed=false,promptEvent=null,busy=false,accepted=false,visits=0,dismissed=false;
 const isInstalled=()=>installed||accepted||media.matches||full.matches||navigator.standalone===true;
 try{
  dismissed=localStorage.getItem('hockey-install-dismissed')==='1';
  visits=Math.max(0,Math.min(2,Number(localStorage.getItem('hockey-install-visits'))||0));
  if(!sessionStorage.getItem('hockey-install-session')){visits=Math.min(2,visits+1);sessionStorage.setItem('hockey-install-session','1');localStorage.setItem('hockey-install-visits',String(visits))}
 }catch{visits=0} // Do not repeatedly suggest installation when dismissal cannot be saved.
 const node=(tag,copy)=>{const n=document.createElement(tag);if(copy)n.textContent=copy;return n};
 function dismiss(){dismissed=true;try{localStorage.setItem('hockey-install-dismissed','1')}catch{}refresh()}
 function showHelp(){const dialog=document.getElementById('install-dialog');if(!dialog.open)dialog.showModal()}
 async function request(){
  if(isInstalled()||busy)return;
  const event=promptEvent;
  if(!event){showHelp();return}
  promptEvent=null;busy=true;refresh();
  try{
   await event.prompt();const choice=await event.userChoice;
   if(choice?.outcome==='accepted')accepted=true;
   if(choice?.outcome==='accepted'||choice?.outcome==='dismissed')dismiss();
  }catch{showHelp()}finally{busy=false;refresh()}
 }
 function button(){const b=node('button',t.install);b.type='button';b.onclick=request;b.disabled=busy;b.dataset.installAction='';return b}
 function refresh(){
  const banner=document.getElementById('install-banner');
  if(!banner)return;
  banner.hidden=isInstalled()||dismissed||visits<2;
  document.querySelectorAll('[data-install-settings]').forEach(n=>n.hidden=isInstalled());
  document.querySelectorAll('[data-install-action]').forEach(b=>b.disabled=busy);
  if(isInstalled()){const d=document.getElementById('install-dialog');if(d.open)d.close()}
 }
 function mountSettings(parent){const f=node('fieldset');f.dataset.installSettings='';f.append(node('legend',t.install),button());f.hidden=isInstalled();parent.append(f)}
 const banner=node('aside');banner.id='install-banner';banner.className='wrap';banner.hidden=true;banner.setAttribute('aria-label',t.install);
 const panel=node('div');panel.className='install-panel';const message=node('p',t.message),actions=node('div');actions.className='install-actions';const close=node('button','×');close.type='button';close.setAttribute('aria-label',t.dismiss);close.onclick=dismiss;actions.append(button(),close);panel.append(message,actions);banner.append(panel);document.querySelector('header').after(banner);
 const dialog=node('dialog');dialog.id='install-dialog';dialog.setAttribute('aria-labelledby','install-title');const title=node('h2',t.help);title.id='install-title';const closeHelp=node('button',t.close);closeHelp.type='button';closeHelp.onclick=()=>dialog.close();dialog.append(title,node('p',t[helpKey]),node('p',t.note),closeHelp);document.body.append(dialog);
 window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();if(isInstalled())return;promptEvent=event;refresh()});
 window.addEventListener('appinstalled',()=>{installed=true;promptEvent=null;dismiss()});
 for(const query of [media,full]){if(query.addEventListener)query.addEventListener('change',refresh);else if(query.addListener)query.addListener(refresh)}
 window.addEventListener('storage',event=>{if(event.key==='hockey-install-dismissed'&&event.newValue==='1'){dismissed=true;refresh()}});
 window.addEventListener('pageshow',refresh);
 window.HockeyInstall={mountSettings};refresh();
})();
