const menu = document.querySelector('#mobile-menu');
menu.setAttribute('aria-label', 'Menyuni ochish');
menu.addEventListener('click', () => document.querySelector('.public-nav').classList.toggle('open'));
