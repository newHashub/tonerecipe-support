const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

// Bundle the existing source file. No upstream fetch or second URL inventory.
const xml = fs.readFileSync(path.join(process.cwd(), 'sitemap.xml'));
const sha256 = crypto.createHash('sha256').update(xml).digest('hex');

module.exports = (request, response) => {
  response.setHeader('Cache-Control', 'no-store');
  response.setHeader('X-Content-Type-Options', 'nosniff');
  if (!['GET', 'HEAD'].includes(request.method)) {
    response.setHeader('Allow', 'GET, HEAD');
    response.statusCode = 405;
    response.end();
    return;
  }

  response.setHeader('Content-Type', 'application/xml; charset=utf-8');
  response.setHeader('Content-Length', xml.length);
  response.statusCode = 200;
  // A user agent alone is not proof of Google identity. Do not log IPs,
  // cookies, query strings, authorization headers, or visitor identifiers.
  console.info(JSON.stringify({
    event: 'sitemap_response',
    method: request.method,
    path: '/sitemap.xml',
    status: 200,
    bytes: xml.length,
    sha256,
    userAgent: String(request.headers['user-agent'] || '').slice(0, 300),
  }));
  response.end(request.method === 'HEAD' ? undefined : xml);
};
