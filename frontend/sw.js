const CACHE_NAME = 'crop-analyzer-v1';
const urlsToCache = [
  './',
  './index.html',
  './manifest.json',
  './icons/android-icon-192x192.png',
  './icons/apple-icon-180x180.png',
  './icons/favicon-32x32.png',
  './icons/favicon-96x96.png'
];

// Install event - cache files
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache).catch(err => {
        console.log('[SW] Cache addAll error:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          return caches.delete(cacheName);
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - NETWORK ONLY (no caching)
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') {
    return;
  }

  // Always try network first
  event.respondWith(
    fetch(event.request)
      .then(response => {
        return response;
      })
      .catch(() => {
        // If offline, return offline message
        return new Response('Offline - unable to fetch resource');
      })
  );
});