# Loaded inside the QuakeMind HTTPS virtual host. API calls keep their existing
# upstream and remain same-origin for Secure, HttpOnly session cookies.
location = /admin {
    absolute_redirect off;
    return 302 /konsol;
}

location ~ ^/(giris|sifre-degistir|ekip|afetzede|konsol)(/.*)?$ {
    root /etc/nginx/conf.d/console/current;
    add_header Cache-Control "no-cache";
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header Referrer-Policy same-origin always;
    try_files /index.html =404;
}

location ^~ /assets/ {
    root /etc/nginx/conf.d/console/current;
    add_header Cache-Control "public, max-age=31536000, immutable";
    add_header X-Content-Type-Options nosniff always;
    try_files $uri =404;
}
