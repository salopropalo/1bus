
import type { User } from '../types/user'

export async function getCurrentUser(): Promise<User> {
  const response = await fetch('/api/me/', {
    method: 'GET',
    credentials: 'include',
  })

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      throw new Error('Пользователь не авторизован')
    }

    throw new Error(`Ошибка сервера: ${response.status}`)
  }

  return response.json()
}
