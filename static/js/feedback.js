(function(){
  const open=document.getElementById('cpcFeedbackOpen'), panel=document.getElementById('cpcFeedbackPanel');
  const close=document.getElementById('cpcFeedbackClose'), submit=document.getElementById('cpcFeedbackSubmit'), track=document.getElementById('cpcFeedbackTrack');
  const message=document.getElementById('cpcFeedbackMessage'), status=document.getElementById('cpcFeedbackStatus'), locationSelect=document.getElementById('cpcFeedbackLocation'), trackCode=document.getElementById('cpcFeedbackTrackCode'), trackStatus=document.getElementById('cpcFeedbackTrackStatus');
  if(!open || !panel || !close || !submit || !track || !message) return;
  let kind='note';
  function show(){
    panel.hidden=false;
    open.setAttribute('aria-expanded','true');
    open.classList.add('is-active');
    if(locationSelect && !locationSelect.value){
      const cur=window.location.pathname;
      for(let i=0; i<locationSelect.options.length; i++){
        if(locationSelect.options[i].value === cur){
          locationSelect.selectedIndex = i;
          break;
        }
      }
    }
    panel.focus({preventScroll:true});
  }
  function hide(){
    panel.hidden=true;
    open.setAttribute('aria-expanded','false');
    open.classList.remove('is-active');
  }
  function toggle(e){
    e && e.preventDefault();
    if(panel.hidden){
      show();
    }else{
      hide();
    }
  }
  open.addEventListener('click',toggle);
  close.addEventListener('click',hide);
  document.addEventListener('keydown',e=>{if(e.key==='Escape' && !panel.hidden){hide();open.focus();}});
  document.addEventListener('click',e=>{if(!panel.hidden && !panel.contains(e.target) && !open.contains(e.target)){hide();}});
  panel.querySelectorAll('[data-kind]').forEach(btn=>btn.addEventListener('click',()=>{kind=btn.dataset.kind;panel.querySelectorAll('[data-kind]').forEach(b=>b.classList.remove('selected'));btn.classList.add('selected');message.focus()}));
  submit.addEventListener('click',async()=>{
    const text=message.value.trim();
    if(!text){status.textContent='Add a quick note so we know what you mean.';status.className='cpc-feedback-status error';message.focus();return}
    const nameEl=document.getElementById('cpcFeedbackName');
    const name=nameEl?nameEl.value.trim():'';
    if(!name){status.textContent='Please add your name.';status.className='cpc-feedback-status error';if(nameEl)nameEl.focus();return}
    submit.disabled=true;status.textContent='Sending…';status.className='cpc-feedback-status';
    const devices=[...document.querySelectorAll('input[name="feedbackDevice"]:checked')].map(input=>input.value);
    const submittedMessage=devices.length ? `[Device: ${devices.join(', ')}]\n\n${text}` : text;
    const websiteEl=document.getElementById('cpcFeedbackWebsite');
    const emailEl=document.getElementById('cpcFeedbackEmail');
    try{
      const response=await fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,message:submittedMessage,name:name,email:emailEl?emailEl.value:'',website:websiteEl?websiteEl.value:'',page_url:(locationSelect&&locationSelect.value)||location.pathname+location.search,page_title:document.title})});
      if(!response.ok) throw new Error();
      const result=await response.json(); message.value=''; submit.disabled=false; status.textContent=`Thank you — your tracking code is ${result.tracking_code}.`;trackCode.value=result.tracking_code;panel.querySelectorAll('[data-kind]').forEach(b=>b.classList.remove('selected'));kind='note';
      setTimeout(hide,1800);
    }catch(e){status.textContent='That didn’t send. Please try again.';status.className='cpc-feedback-status error';submit.disabled=false}
  });
  track.addEventListener('click',async()=>{const code=trackCode.value.trim();if(!code){trackStatus.textContent='Enter your tracking code first.';return}try{const response=await fetch('/api/feedback/'+encodeURIComponent(code));const result=await response.json();if(!response.ok)throw new Error();trackStatus.textContent=`Status: ${result.status.replaceAll('-',' ')}${result.review_note?' — '+result.review_note:''}`;}catch(e){trackStatus.textContent='We couldn’t find that feedback code.';trackStatus.className='cpc-feedback-status error'}});
})();
