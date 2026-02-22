import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory('/'),
    routes: [
        {
            path: '/video-player',
            name: 'PlayerView',
            component: () => import('@/views/UploadPlayerView.vue'),
            meta: { requiresAuth: true, requiresVerification: true }
        },
    ],
})

export default router