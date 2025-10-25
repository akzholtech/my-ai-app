document.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("access_token");
  if (!token) {
    // Not logged in → redirect
    window.location.href = "/login";
    return;
  }

  try {
    // Verify token with backend
    const res = await fetch("/auth/verify-token", {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` }
    });

    if (!res.ok) throw new Error("Invalid token");

    // Token valid → show page
    console.log("Authenticated!");
  } catch (err) {
    console.warn(err.message);
    localStorage.removeItem("access_token");
    window.location.href = "/login";
  }
});