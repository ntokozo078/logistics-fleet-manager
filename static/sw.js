self.addEventListener('install', function(event) {
  console.log('Service Worker installing.');
});

self.addEventListener('fetch', function(event) {
  // Simple pass-through (so the app works online)
  event.respondWith(fetch(event.request));
});
const CACHE_NAME = 'logistics-pro-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/dashboard',
    '/static/manifest.json',
    '/static/logo.svg',
    'https://cdn.tailwindcss.com',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap'
];

// 1. Install Event: Cache the "App Shell"
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[Service Worker] Caching App Shell');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

// 2. Fetch Event: Serve from Cache if Offline
self.addEventListener('fetch', (event) => {
    // Only handle GET requests (pages, images, styles)
    if (event.request.method !== 'GET') return;

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }
            // If not in cache, fetch from network
            return fetch(event.request).catch(() => {
                // If network fails (offline) and not in cache, you could show a custom offline page
                // For now, we just let it fail gracefully or show a cached dashboard if available
            });
        })
    );
});

// 3. Activate Event: Clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keyList) => {
            return Promise.all(keyList.map((key) => {
                if (key !== CACHE_NAME) {
                    return caches.delete(key);
                }
            }));
        })
    );
});