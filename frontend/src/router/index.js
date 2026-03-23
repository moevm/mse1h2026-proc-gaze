import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory('/'),
    routes: [
        {
            path: '/upload-video',
            name: 'UploadPlayerView',
            component: () => import('@/views/UploadPlayerView.vue'),
            meta: { requiresAuth: true, requiresVerification: true }
        },
        {
            path: '/main',
            name: 'MainView',
            component: () => import('@/views/MainView.vue'),
            meta: { requiresAuth: true, requiresVerification: true }
        },
        {
            path: '/result',
            name: 'ResultView',
            component: () => import('@/views/ResultView.vue'),
            meta: { requiresAuth: true, requiresVerification: true }
        }
    ],
})

export default router