const form = document.getElementById('loginForm');
const btn  = document.getElementById('loginBtn');
const msg  = document.getElementById('msg');
if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const name = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value;

      if (!username || !password) {
        msg.textContent = 'Please enter username and password.';
        return;
      }

      btn.disabled = true; msg.textContent = 'Signing in...';

      try {
        const res = await fetch('/api/login', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({name, password}),
              });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `HTTP ${res.status}`);
        } else {
            const data = await res.json();
            msg.textContent = 'Success! Redirecting...';
            localStorage.setItem('access_token', data.access_token);
            window.location.href = '/dashboard'
        }
    }
      catch (err) {
        msg.textContent = `Login failed: ${err.message}`;
      } finally {
      console.log("Finished!")
      }
        btn.disabled = false;

    });
    }


function logout() {
    localStorage.removeItem("access_token");
    window.location.href = 'login';
}