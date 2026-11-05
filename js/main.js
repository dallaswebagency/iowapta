(function(){
  var b=document.getElementById('burger'),m=document.getElementById('menu');
  if(b&&m){
    b.addEventListener('click',function(){var o=m.classList.toggle('open');b.setAttribute('aria-expanded',o)});
  }
  // dropdown toggles (tap on touch / mobile, keyboard on desktop)
  document.querySelectorAll('.sub-toggle').forEach(function(t){
    t.addEventListener('click',function(e){
      e.preventDefault();
      var li=t.parentNode,o=!li.classList.contains('open');
      document.querySelectorAll('.has-sub.open').forEach(function(x){if(x!==li){x.classList.remove('open');x.querySelector('.sub-toggle').setAttribute('aria-expanded',false)}});
      li.classList.toggle('open',o);t.setAttribute('aria-expanded',o);
    });
  });
  document.addEventListener('click',function(e){
    if(!e.target.closest('.has-sub')&&window.innerWidth>900){
      document.querySelectorAll('.has-sub.open').forEach(function(x){x.classList.remove('open');x.querySelector('.sub-toggle').setAttribute('aria-expanded',false)});
    }
  });
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape'){document.querySelectorAll('.has-sub.open').forEach(function(x){x.classList.remove('open')});if(m)m.classList.remove('open');}
  });
  // close the mobile menu after jumping to an on-page anchor
  if(m)m.addEventListener('click',function(e){var a=e.target.closest('a');if(a&&a.getAttribute('href').indexOf('#')>-1){m.classList.remove('open');b&&b.setAttribute('aria-expanded',false)}});
})();
