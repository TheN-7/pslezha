const http = require("http");
const fs = require("fs");
const path = require("path");

const port = Number(process.env.PORT || 3000);
const faqDir = path.resolve(__dirname, "..", "faq");

const pages = {
  "/": "PS - Dega Lezhe (6_1_2026 10：51：12 AM).html",
  "/dashboard": "PS - Dega Lezhe (6_1_2026 10：51：12 AM).html",
  "/structure": "PS - Dega Lezhe (6_1_2026 10：53：09 AM).html",
  "/electoral-list": "PS - Dega Lezhe (6_1_2026 10：53：22 AM).html",
  "/families": "PS - Dega Lezhe (6_1_2026 10：53：29 AM).html",
  "/emigrants": "PS - Dega Lezhe (6_1_2026 10：53：37 AM).html",
  "/patronage-workers": "PS - Dega Lezhe (6_1_2026 10：53：49 AM).html"
};

function normalizePath(url) {
  const requestUrl = new URL(url, `http://localhost:${port}`);
  const pathname = requestUrl.pathname.replace(/\/+$/, "") || "/";
  return pages[pathname] ? pathname : null;
}

function localizeLinks(html) {
  return html
    .replaceAll("http://pslezha.com/dashboard", "/dashboard")
    .replaceAll("http://pslezha.com/structure", "/structure")
    .replaceAll("http://pslezha.com/electoral-list", "/electoral-list")
    .replaceAll("http://pslezha.com/families", "/families")
    .replaceAll("http://pslezha.com/emigrants", "/emigrants")
    .replaceAll("http://pslezha.com/patronage-workers", "/patronage-workers");
}

const server = http.createServer((req, res) => {
  const route = normalizePath(req.url);

  if (!route) {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Page not found");
    return;
  }

  const filePath = path.join(faqDir, pages[route]);

  fs.readFile(filePath, "utf8", (err, html) => {
    if (err) {
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end(`Could not read ${pages[route]}`);
      return;
    }

    res.writeHead(200, {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store"
    });
    res.end(localizeLinks(html));
  });
});

server.listen(port, () => {
  console.log(`Static visual copy running at http://localhost:${port}`);
});
