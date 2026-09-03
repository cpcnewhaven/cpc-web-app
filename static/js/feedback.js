(function(){
  const open=document.getElementById('cpcFeedbackOpen'), panel=document.getElementById('cpcFeedbackPanel');
  const close=document.getElementById('cpcFeedbackClose'), submit=document.getElementById('cpcFeedbackSubmit');
  const message=document.getElementById('cpcFeedbackMessage'), status=document.getElementById('cpcFeedbackStatus');
  let kind='note';
  function show(){panel.hidden=false;open.hidden=true;open.setAttribute('aria-expanded','true');message.focus()}
  function hide(){panel.hidden=true;open.hidden=false;open.setAttribute('aria-expanded','false')}
  open.addEventListener('click',show); close.addEventListener('click',hide);
  panel.querySelectorAll('[data-kind]').forEach(btn=>btn.addEventListener('click',()=>{kind=btn.dataset.kind;panel.querySelectorAll('[data-kind]').forEach(b=>b.classList.remove('selected'));btn.classList.add('selected');message.focus()}));
  submit.addEventListener('click',async()=>{
    const text=message.value.trim();
    if(!text){status.textContent='Add a quick note so we know what you mean.';status.className='cpc-feedback-status error';message.focus();return}
    submit.disabled=true;status.textContent='Sending…';status.className='cpc-feedback-status';
    try{const response=await fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,message:text,name:document.getElementById('cpcFeedbackName').value,email:document.getElementById('cpcFeedbackEmail').value,page_url:location.pathname+location.search,page_title:document.title})});
      if(!response.ok) throw new Error();
      message.value='';status.textContent='Thank you — that helps us make this better. ✨';panel.querySelectorAll('[data-kind]').forEach(b=>b.classList.remove('selected'));kind='note';
      setTimeout(hide,1800);
    }catch(e){status.textContent='That didn’t send. Please try again.';status.className='cpc-feedback-status error';submit.disabled=false}
  });
})();
