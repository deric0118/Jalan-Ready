document.addEventListener("DOMContentLoaded", () => {
  // Detect environment: localhost = development, otherwise = production
  const BACKEND_BASE_URL =
    window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      ? 'http://127.0.0.1:8000'
      : 'https://api.jalan-ready.tk'; // Replace with your actual production API URL
  
  const LOGIN_ENDPOINT = `${BACKEND_BASE_URL}/api/login`;
  const SIGNUP_ENDPOINT = `${BACKEND_BASE_URL}/api/signup`;
  const REDIRECT_URL = "frontend/index.html";

  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const formLogin = document.getElementById("form-login");
  const formRegister = document.getElementById("form-register");
  const loginMessage = document.getElementById("login-message");
  const registerMessage = document.getElementById("register-message");

  if (!tabLogin || !tabRegister || !formLogin || !formRegister) {
    return;
  }

  const setMessage = (element, text, isError = false) => {
    if (!element) return;
    element.textContent = text;
    element.classList.remove("text-red-500", "text-green-600", "text-slate-500");
    if (isError) {
      element.classList.add("text-red-500");
      return;
    }
    if (text) {
      element.classList.add("text-green-600");
      return;
    }
    element.classList.add("text-slate-500");
  };

  const setSubmitting = (button, submittingText, isSubmitting) => {
    if (!button) return;
    if (isSubmitting) {
      button.dataset.originalText = button.innerHTML;
      button.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> ${submittingText}`;
      button.disabled = true;
      return;
    }
    button.innerHTML = button.dataset.originalText || button.innerHTML;
    button.disabled = false;
  };

  const switchToLogin = () => {
    tabLogin.classList.add("bg-white", "shadow-sm", "font-semibold", "text-sirca-navy");
    tabLogin.classList.remove("font-medium", "text-slate-500", "hover:text-slate-700");
    tabRegister.classList.remove("bg-white", "shadow-sm", "font-semibold", "text-sirca-navy");
    tabRegister.classList.add("font-medium", "text-slate-500", "hover:text-slate-700");
    formRegister.classList.add("hidden");
    formLogin.classList.remove("hidden");
    setMessage(registerMessage, "");
  };

  const switchToRegister = () => {
    tabRegister.classList.add("bg-white", "shadow-sm", "font-semibold", "text-sirca-navy");
    tabRegister.classList.remove("font-medium", "text-slate-500", "hover:text-slate-700");
    tabLogin.classList.remove("bg-white", "shadow-sm", "font-semibold", "text-sirca-navy");
    tabLogin.classList.add("font-medium", "text-slate-500", "hover:text-slate-700");
    formLogin.classList.add("hidden");
    formRegister.classList.remove("hidden");
    setMessage(loginMessage, "");
  };

  tabLogin.addEventListener("click", switchToLogin);
  tabRegister.addEventListener("click", switchToRegister);

  formLogin.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = formLogin.querySelector('button[type="submit"]');
    setMessage(loginMessage, "");
    setSubmitting(submitButton, "Authenticating...", true);

    const payload = {
      email: document.getElementById("login-email")?.value?.trim(),
      password: document.getElementById("login-password")?.value || "",
    };

    try {
      const response = await fetch(LOGIN_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Login failed. Please check your credentials.");
      }

      localStorage.setItem("auth_token", data.token || "");
      localStorage.setItem("auth_user", JSON.stringify(data.user || { email: payload.email }));
      setMessage(loginMessage, "Login successful. Redirecting...");
      window.location.href = REDIRECT_URL;
    } catch (error) {
      setMessage(loginMessage, error.message || "Unable to login.", true);
    } finally {
      setSubmitting(submitButton, "", false);
    }
  });

  formRegister.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = formRegister.querySelector('button[type="submit"]');
    setMessage(registerMessage, "");
    setSubmitting(submitButton, "Creating account...", true);

    const payload = {
      name: document.getElementById("register-name")?.value?.trim(),
      email: document.getElementById("register-email")?.value?.trim(),
      password: document.getElementById("register-password")?.value || "",
      phone_number: document.getElementById("register-phone-number")?.value?.trim(),
      id_number: document.getElementById("register-id-number")?.value?.trim(),
      address: document.getElementById("register-address")?.value?.trim(),
      postcode: document.getElementById("register-postcode")?.value?.trim(),
    };

    try {
      const response = await fetch(SIGNUP_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Sign up failed. Please verify your details.");
      }

      localStorage.setItem("auth_token", data.token || "");
      localStorage.setItem("auth_user", JSON.stringify(data.user || { email: payload.email, name: payload.name }));
      setMessage(registerMessage, "Account created successfully. Redirecting...");
      window.location.href = REDIRECT_URL;
    } catch (error) {
      setMessage(registerMessage, error.message || "Unable to create account.", true);
    } finally {
      setSubmitting(submitButton, "", false);
    }
  });
});