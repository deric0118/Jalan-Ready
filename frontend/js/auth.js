/**
 * ═══════════════════════════════════════════════════════════════════
 * auth.js  —  SIRCa Authentication Controller
 * Handles the toggle between Login and Register, and mock auth submission.
 * ═══════════════════════════════════════════════════════════════════
 */

document.addEventListener('DOMContentLoaded', () => {
  const tabLogin    = document.getElementById('tab-login');
  const tabRegister = document.getElementById('tab-register');
  const formLogin   = document.getElementById('form-login');
  const formRegister= document.getElementById('form-register');

  // --- Toggle Logic ---
  tabLogin.addEventListener('click', () => {
    // 激活 Login 样式
    tabLogin.classList.replace('text-slate-500', 'text-sirca-navy');
    tabLogin.classList.replace('hover:text-slate-700', 'bg-white');
    tabLogin.classList.add('shadow-sm', 'font-semibold');
    tabLogin.classList.remove('font-medium');

    // 变暗 Register 样式
    tabRegister.classList.replace('text-sirca-navy', 'text-slate-500');
    tabRegister.classList.replace('bg-white', 'hover:text-slate-700');
    tabRegister.classList.remove('shadow-sm', 'font-semibold');
    tabRegister.classList.add('font-medium');

    // 切换表单显示
    formRegister.classList.add('hidden');
    formLogin.classList.remove('hidden');
  });

  tabRegister.addEventListener('click', () => {
    // 激活 Register 样式
    tabRegister.classList.replace('text-slate-500', 'text-sirca-navy');
    tabRegister.classList.replace('hover:text-slate-700', 'bg-white');
    tabRegister.classList.add('shadow-sm', 'font-semibold');
    tabRegister.classList.remove('font-medium');

    // 变暗 Login 样式
    tabLogin.classList.replace('text-sirca-navy', 'text-slate-500');
    tabLogin.classList.replace('bg-white', 'hover:text-slate-700');
    tabLogin.classList.remove('shadow-sm', 'font-semibold');
    tabLogin.classList.add('font-medium');

    // 切换表单显示
    formLogin.classList.add('hidden');
    formRegister.classList.remove('hidden');
  });

  // --- Mock Authentication Submission ---
  formLogin.addEventListener('submit', (e) => {
    e.preventDefault();
    const btn = formLogin.querySelector('button[type="submit"]');
    btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Authenticating...`;
    btn.disabled = true;

   
    setTimeout(() => {
     
      localStorage.setItem('sirca_user', 'admin');
      window.location.href = 'index.html';
    }, 1200);
  });

  formRegister.addEventListener('submit', (e) => {
    e.preventDefault();
    const btn = formRegister.querySelector('button[type="submit"]');
    btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Creating Account...`;
    btn.disabled = true;

    setTimeout(() => {
      localStorage.setItem('sirca_user', 'new_user');
      window.location.href = 'index.html';
    }, 1500);
  });
});