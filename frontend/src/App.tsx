import { useEffect, useState } from 'react'

import { getCurrentUser } from './api/users'
import {
  getCsrfToken,
  loginUser,
  logoutUser,
} from './api/auth'

import type { User } from './types/user'
import './App.css'

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [csrfToken, setCsrfToken] = useState('')

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    async function initialize() {
      try {
        const token = await getCsrfToken()
        setCsrfToken(token)

        try {
          const currentUser = await getCurrentUser()
          setUser(currentUser)
        } catch (err) {
          if (
            err instanceof Error &&
            err.message !== 'Пользователь не авторизован'
          ) {
            throw err
          }
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Ошибка подключения к серверу'
        )
      } finally {
        setLoading(false)
      }
    }

    initialize()
  }, [])

  async function handleLogin(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const loggedUser = await loginUser(
        username,
        password,
        csrfToken
      )

      setUser(loggedUser)
      setPassword('')
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Ошибка авторизации'
      )
    } finally {
      setSubmitting(false)
    }
  }

  async function handleLogout() {
    setError('')
    setSubmitting(true)

    try {
      await logoutUser(csrfToken)
      setUser(null)
      setPassword('')
      setUsername('')
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Ошибка выхода'
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <div className="page">Подключение к системе...</div>
  }

  if (!user) {
    return (
      <div className="login-page">
        <form className="login-card" onSubmit={handleLogin}>
          <div className="login-logo">1BUS</div>

          <h1>Вход в систему</h1>

          <p className="login-description">
            Производственная система управления
          </p>

          <label htmlFor="username">Логин</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            required
          />

          <label htmlFor="password">Пароль</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={submitting}>
            {submitting ? 'Выполняется вход...' : 'Войти'}
          </button>
        </form>
      </div>
    )
  }

  const fullName =
    `${user.first_name} ${user.last_name}`.trim() ||
    user.username

  return (
    <div className="app">
      <header className="header">
        <div className="logo">1BUS</div>

        <div className="header-title">
          Производственная система
        </div>

        <div className="header-user">
          <span>{fullName}</span>

          <button
            className="logout-button"
            onClick={handleLogout}
            disabled={submitting}
          >
            Выйти
          </button>
        </div>
      </header>

      <main className="main">
        <div className="welcome">
          <p className="eyebrow">ЛИЧНЫЙ КАБИНЕТ</p>

          <h1>Добро пожаловать, {fullName}!</h1>

          <p className="subtitle">
            Вы вошли в производственную систему 1BUS.
          </p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <section className="user-card">
          <h2>Информация о пользователе</h2>

          <div className="user-grid">
            <div className="user-field">
              <span>ID пользователя</span>
              <strong>{user.id}</strong>
            </div>

            <div className="user-field">
              <span>Логин</span>
              <strong>{user.username}</strong>
            </div>

            <div className="user-field">
              <span>Имя</span>
              <strong>{user.first_name || 'Не указано'}</strong>
            </div>

            <div className="user-field">
              <span>Фамилия</span>
              <strong>{user.last_name || 'Не указана'}</strong>
            </div>

            <div className="user-field">
              <span>Email</span>
              <strong>{user.email || 'Не указан'}</strong>
            </div>

            <div className="user-field">
              <span>Сотрудник</span>
              <strong>{user.is_staff ? 'Да' : 'Нет'}</strong>
            </div>

            <div className="user-field">
              <span>Администратор</span>
              <strong>{user.is_superuser ? 'Да' : 'Нет'}</strong>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
