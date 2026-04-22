import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory('/'),
    routes: [
        {
            path: '/',
            redirect: '/main'
        },
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
            path: '/result/:recording_id',
            name: 'ResultView',
            component: () => import('@/views/ResultView.vue'),
            meta: { requiresAuth: true, requiresVerification: true }
        },
        {
            path: '/dump-students',
            name: 'DumpStudentView',
            component: () => import('@/views/DumpStudentView.vue'),
            meta: { requiresAuth: true, requiresVerification: true }
        },
        {
            path: '/calibration',
            name: 'CalibrationView',
            component: () => import('@/views/CalibrationView.vue'),
            meta: { requiresAuth: true, requiresVerification: true }
        }
    ],
})

export default router