import type { User } from '../types/user'

const API_URL = '/api'

export async function getCsrfToken(): Promise<string> {
  const response = await fetch(`${API_URL}/csrf/`, {
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error('Не удалось получить CSRF-токен')
  }

  const data = await response.json()
  return data.csrfToken
}

export async function loginUser(
  username: string,
  password: string,
  csrfToken: string
): Promise<User> {
  const response = await fetch(`${API_URL}/login/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({ username, password }),
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.detail || 'Ошибка авторизации')
  }

  return data.user
}

export async function logoutUser(
  csrfToken: string
): Promise<void> {
  const response = await fetch(`${API_URL}/logout/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRFToken': csrfToken,
    },
  })

  if (!response.ok) {
    throw new Error('Не удалось завершить сеанс')
  }
}
