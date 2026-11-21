
import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import type { User } from '../types/user'

interface MainLayoutProps {
  user: User
  onLogout: () => void
  submitting: boolean
}

export default function MainLayout({
  user,
  onLogout,
  submitting,
}: MainLayoutProps) {
  const fullName =
    `${user.first_name} ${user.last_name}`.trim() ||
    user.username

  return (
    <div className="app-layout">
      <Sidebar />

      <div className="app-content">
        <header className="topbar">
          <div className="topbar-title">
            Производственная система
          </div>

          <div className="topbar-user">
            <div className="user-avatar">
              {fullName.charAt(0).toUpperCase()}
            </div>

            <div className="topbar-user-info">
              <strong>{fullName}</strong>
              <span>{user.is_superuser ? 'Администратор' : 'Сотрудник'}</span>
            </div>

            <button
              className="logout-button"
              onClick={onLogout}
              disabled={submitting}
            >
              Выйти
            </button>
          </div>
        </header>

        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
