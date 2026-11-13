const USER_ID_KEY = "shopfront_user_id";
const TOKEN_KEY = "shopfront_token";

export function getUserId(): string {
  return localStorage.getItem(USER_ID_KEY) ?? "guest-user";
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setSession(userId: string, token: string) {
  localStorage.setItem(USER_ID_KEY, userId);
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearSession() {
  localStorage.removeItem(USER_ID_KEY);
  localStorage.removeItem(TOKEN_KEY);
}
