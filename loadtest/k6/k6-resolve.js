import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '15s', target: 20 },
    { duration: '30s', target: 100 },
    { duration: '30s', target: 200 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<500'],
    http_req_failed:   ['rate<0.01'],
  },
};

const HOST = __ENV.HOST || 'http://api-gateway:8080';
const CODE = __ENV.CODE;

export default function () {
  const res = http.get(`${HOST}/${CODE}`, { redirects: 0 });
  check(res, {
    'status is 301': (r) => r.status === 301,
    'has Location':  (r) => r.headers['Location'] !== undefined,
  });
}
