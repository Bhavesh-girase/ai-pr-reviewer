import { createBrowserRouter } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import LandingPage from './pages/LandingPage'
import DashboardPage from './pages/DashboardPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailsPage from './pages/ProjectDetailsPage'
import PullRequestDetailsPage from './pages/PullRequestDetailsPage'
import ReviewDetailsPage from './pages/ReviewDetailsPage'
import SettingsPage from './pages/SettingsPage'
import NotFoundPage from './pages/NotFoundPage'
import Login from './pages/Login'
import Register from './pages/Register'
import ProtectedRoute from './components/ProtectedRoute'

export const router = createBrowserRouter([
  // Public landing page
  {
    path: '/',
    element: <LandingPage />,
  },

  // Authenticated app shell
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'projects',
        element: <ProjectsPage />,
      },
      {
        path: 'projects/:projectId',
        element: <ProjectDetailsPage />,
      },
      {
        path: 'projects/:projectId/pull-requests',
        element: <ProjectDetailsPage defaultTab="pulls" />,
      },
      {
        path: 'projects/:projectId/pull-requests/:prNumber',
        element: <PullRequestDetailsPage />,
      },
      {
        path: 'projects/:projectId/reviews',
        element: <ProjectDetailsPage defaultTab="reviews" />,
      },
      {
        path: 'projects/:projectId/reviews/:reviewId',
        element: <ReviewDetailsPage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },

  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/register',
    element: <Register />,
  },
])
