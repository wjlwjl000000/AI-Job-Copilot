import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/chat', name: 'Chat', component: () => import('../views/Chat.vue') },
  { path: '/profile', name: 'Profile', component: () => import('../views/Profile.vue') },
  { path: '/resumes', name: 'Resumes', component: () => import('../views/Resumes.vue') },
  { path: '/jobs', name: 'JobMatch', component: () => import('../views/JobMatch.vue') },
  { path: '/applications', name: 'Applications', component: () => import('../views/Applications.vue') },
  { path: '/interview', name: 'InterviewPrep', component: () => import('../views/InterviewPrep.vue') },
  { path: '/support', name: 'SupportFeed', component: () => import('../views/SupportFeed.vue') },
  { path: '/agents', name: 'AgentRegistry', component: () => import('../views/AgentRegistry.vue') },
]

const router = createRouter({ history: createWebHistory(), routes })
export default router
