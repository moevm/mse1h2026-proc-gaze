import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import {createPinia} from "pinia";
import { library } from '@fortawesome/fontawesome-svg-core';
import { faChevronDown, faChevronUp } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

const pinia = createPinia()

library.add(faChevronDown, faChevronUp);

const app = createApp(App)
app.component('font-awesome-icon', FontAwesomeIcon);
app.use(pinia)
app.use(router)
app.mount('#app')
