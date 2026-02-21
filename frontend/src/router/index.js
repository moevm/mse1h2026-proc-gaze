import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory('/'),
    routes: [
        {
            path: '/video-player',
            name: 'VideoPlayer',
            // component: () => import('@/components/VideoPlayer.vue'),
            meta: { requiresAuth: true, requiresVerification: true }
        },
    ],
})

export default router