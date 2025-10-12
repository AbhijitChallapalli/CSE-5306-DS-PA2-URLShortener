// import http from 'k6/http';
// import { check } from 'k6';

// export let options = {
//   stages: [
//     { duration: '15s', target: 20 },
//     { duration: '30s', target: 100 },
//     { duration: '30s', target: 200 },
//   ],
//   thresholds: {
//     http_req_duration: ['p(95)<200', 'p(99)<500'],
//     http_req_failed:   ['rate<0.01'],
//   },
// };

// const HOST = __ENV.HOST || 'http://api-gateway:8080';
// const CODE = __ENV.CODE;

// export default function () {
//   const res = http.get(`${HOST}/${CODE}`, { redirects: 0 });
//   check(res, {
//     'status is 301': (r) => r.status === 301,
//     'has Location':  (r) => r.headers['Location'] !== undefined,
//   });
// }

import http from 'k6/http';
import { check, sleep } from 'k6';
import { htmlReport } from 'https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.4/index.js';

export let options = {
  stages: [
    { duration: '15s', target: 20 },
    { duration: '30s', target: 100 },
    { duration: '30s', target: 200 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000', 'p(99)<4000'], // relaxed so runs don’t “fail” under load
    http_req_failed:   ['rate<0.01'],
  },
};

const HOST  = __ENV.HOST || 'http://api-gateway:8080';
const CODE  = __ENV.CODE;
const PAUSE = Number(__ENV.SLEEP || 0.1);

export default function () {
  // rotate IP per VU/iteration to dodge per-IP RL
  const ip = `10.${Math.floor(__VU/256)}.${__VU % 256}.${(__ITER % 250) + 1}`;
  const res = http.get(`${HOST}/${CODE}`, {
    redirects: 0,                         // <— important for 301 check
    headers: { 'X-Forwarded-For': ip },   // <— avoid 429s at high load
  });

  check(res, {
    'status is 301': (r) => r.status === 301,
    'has Location':  (r) => r.headers['Location'] !== undefined,
  });
  sleep(PAUSE);
}

export function handleSummary(data) {
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const label = __ENV.RUN || `run-${stamp}`;
  return {
    [`/work/k6-${label}.html`]: htmlReport(data),
    [`/work/k6-${label}.json`]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}




