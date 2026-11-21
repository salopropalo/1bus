
import { NavLink } from 'react-router-dom'

const menuItems = [
  {
    title: 'Рабочий стол',
    path: '/',
    icon: '⌂',
  },
  {
    title: 'Компании',
    path: '/companies',
    icon: '▤',
  },
  {
    title: 'Запросы клиентов',
    path: '/requests',
    icon: '▧',
  },
  {
    title: 'Сделки',
    path: '/deals',
    icon: '◇',
  },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">1BUS</div>
        <div className="sidebar-caption">CRM SYSTEM</div>
      </div>

      <div className="sidebar-section-title">
        РАБОТА
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? 'active' : ''}`
            }
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span>{item.title}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="sidebar-version">
          1BUS · CRM
          <br />
          Версия 0.1
        </div>
      </div>
    </aside>
  )
}
