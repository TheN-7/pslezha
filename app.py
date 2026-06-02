import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
import pymysql
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "users.db"
LOCAL_VOTERS_DATABASE = BASE_DIR / "dogana.db"

PAGES = {
    "dashboard": "dashboard.html",
    "structure": "structure.html",
    "electoral-list": "electoral-list.html",
    "families": "families.html",
    "emigrants": "emigrants.html",
    "patronage-workers": "patronage-workers.html",
}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-local-dev-secret")


def find_first_existing(*paths):
    for path in paths:
        if path.exists():
            return path
    return paths[0]


def load_env_file():
    env_path = find_first_existing(BASE_DIR / ".env", BASE_DIR.parent / ".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_env_file()
app.secret_key = os.environ.get("SECRET_KEY", app.secret_key)
LOCAL_VOTERS_DATABASE = find_first_existing(
    BASE_DIR / "dogana.db", BASE_DIR.parent / "dogana.db"
)


def db_connect():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def voters_db_driver():
    return os.environ.get("VOTERS_DB_DRIVER", "sqlite").strip().lower()


def mysql_host_and_port():
    host = os.environ.get("VOTERS_DB_HOST", "localhost").strip()
    port = int(os.environ.get("VOTERS_DB_PORT", "3306"))

    if ":" in host and not host.startswith("["):
        host_part, port_part = host.rsplit(":", 1)
        if port_part.isdigit():
            host = host_part
            port = int(port_part)

    return host, port


def voters_db_connect():
    if voters_db_driver() == "mysql":
        host, port = mysql_host_and_port()
        return pymysql.connect(
            host=host,
            port=port,
            user=os.environ["VOTERS_DB_USER"],
            password=os.environ["VOTERS_DB_PASSWORD"],
            database=os.environ["VOTERS_DB_NAME"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

    connection = sqlite3.connect(LOCAL_VOTERS_DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db_connect() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?", ("admin",)
        ).fetchone()
        if existing is None:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                ("admin", generate_password_hash("admin123")),
            )


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def electoral_search_script():
    return f"""
<script>
(function () {{
  const input = Array.from(document.querySelectorAll('input')).find(function (element) {{
    return (element.getAttribute('placeholder') || '').toLowerCase().includes('votues');
  }});
  const table = document.querySelector('table');
  const tbody = table ? table.querySelector('tbody') : null;
  const countText = document.querySelector('.border-t .text-sm.text-muted-foreground');
  if (!input || !tbody) return;

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, function (char) {{
    return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[char];
  }});

  const badge = (value) => {{
    const text = value || 'NO_INFORMATION';
    return '<button type="button" role="combobox" class="flex items-center justify-between rounded-md border border-input text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 h-8 border-none bg-transparent shadow-none w-fit font-medium p-0 focus:ring-0 gap-2"><div class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 text-foreground">' + escapeHtml(text) + '</div></button>';
  }};

  const referrer = (value) => {{
    const text = value || '-';
    return '<button class="inline-flex items-center gap-2 whitespace-nowrap rounded-md text-sm ring-offset-background transition-colors border border-input py-2 justify-between h-8 border-none bg-transparent hover:bg-accent hover:text-accent-foreground shadow-none px-2 shrink-0 w-fit font-medium" role="combobox" type="button"><span class="text-muted-foreground">' + escapeHtml(text) + '</span></button>';
  }};

  const eyeButton = '<div class="flex items-center justify-end gap-2"><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors hover:bg-accent hover:text-accent-foreground h-8 w-8" title="Shiko"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-eye h-4 w-4"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"></path><circle cx="12" cy="12" r="3"></circle></svg></button></div>';

  const td = (value, classes = 'text-sm') => '<td class="p-4 align-middle [&amp;:has([role=checkbox])]:pr-0 ' + classes + '">' + escapeHtml(value) + '</td>';

  const renderRows = (rows) => {{
    if (!rows.length) {{
      tbody.innerHTML = '<tr class="border-b"><td class="p-6 text-center text-muted-foreground" colspan="11">Nuk u gjet asnje votues</td></tr>';
      if (countText) countText.textContent = 'Duke shfaqur 0 rezultate';
      return;
    }}

    tbody.innerHTML = rows.map(function (row, index) {{
      return '<tr class="border-b transition-colors data-[state=selected]:bg-muted hover:bg-muted/50">' +
        td(index + 1, 'font-medium') +
        td(row.first_name) +
        td(row.last_name) +
        td(row.fathers_name) +
        td(row.mothers_name) +
        td(row.birthday) +
        td(row.admin_unit) +
        td(row.age) +
        '<td class="p-4 align-middle [&amp;:has([role=checkbox])]:pr-0">' + badge(row.political_preference) + '</td>' +
        '<td class="p-4 align-middle [&amp;:has([role=checkbox])]:pr-0">' + referrer(row.job_referrer) + '</td>' +
        '<td class="p-4 align-middle [&amp;:has([role=checkbox])]:pr-0 text-right">' + eyeButton + '</td>' +
      '</tr>';
    }}).join('');
    if (countText) countText.textContent = 'Duke shfaqur 1 deri ' + rows.length + ' nga ' + rows.length + ' rezultate';
  }};

  const renderMessage = (message) => {{
    tbody.innerHTML = '<tr class="border-b"><td class="p-6 text-center text-muted-foreground" colspan="11">' + escapeHtml(message) + '</td></tr>';
    if (countText) countText.textContent = message;
  }};

  let timer = null;
  let controller = null;

  const search = () => {{
    const query = input.value.trim();
    if (query.length < 2) {{
      renderMessage('Shkruani te pakten 2 karaktere per kerkim');
      return;
    }}
    if (controller) controller.abort();
    controller = new AbortController();
    fetch('{url_for("api_voter_search")}?q=' + encodeURIComponent(query), {{ signal: controller.signal }})
      .then((response) => response.json().then((data) => {{
        if (!response.ok) throw new Error(data.error || 'Kerkimi deshtoi');
        return data;
      }}))
      .then((data) => renderRows(data.results || []))
      .catch((error) => {{
        if (error.name !== 'AbortError') renderMessage(error.message || 'Kerkimi deshtoi');
      }});
  }};

  input.addEventListener('input', function () {{
    window.clearTimeout(timer);
    timer = window.setTimeout(search, 250);
  }});
}})();
</script>
"""


def localize_page(html, page_name=None):
    replacements = {
        "dashboard.html": url_for("page", page_name="dashboard"),
        "structure.html": url_for("page", page_name="structure"),
        "electoral-list.html": url_for("page", page_name="electoral-list"),
        "families.html": url_for("page", page_name="families"),
        "emigrants.html": url_for("page", page_name="emigrants"),
        "patronage-workers.html": url_for("page", page_name="patronage-workers"),
        "http://pslezha.com/dashboard": url_for("page", page_name="dashboard"),
        "http://pslezha.com/structure": url_for("page", page_name="structure"),
        "http://pslezha.com/electoral-list": url_for(
            "page", page_name="electoral-list"
        ),
        "http://pslezha.com/families": url_for("page", page_name="families"),
        "http://pslezha.com/emigrants": url_for("page", page_name="emigrants"),
        "http://pslezha.com/patronage-workers": url_for(
            "page", page_name="patronage-workers"
        ),
    }

    for old, new in replacements.items():
        html = html.replace(old, new)

    extra_script = ""
    if page_name == "electoral-list":
        extra_script += electoral_search_script()

    logout_script = f"""
<script>
document.addEventListener("click", function (event) {{
  const button = event.target.closest("button");
  if (!button || !button.textContent.includes("Dilni")) return;
  window.location.href = "{url_for("logout")}";
}});
</script>
"""
    scripts = f"{extra_script}{logout_script}"
    if "</body>" in html:
        return html.replace("</body>", f"{scripts}</body>")
    return f"{html}{scripts}"


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("page", page_name="dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    next_url = request.args.get("next") or url_for("page", page_name="dashboard")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with db_connect() as db:
            user = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(request.form.get("next") or next_url)

        error = "Invalid username or password"

    return render_template("login.html", error=error, next_url=next_url)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/db/status")
@login_required
def api_db_status():
    driver = voters_db_driver()
    status = {"driver": driver}

    if driver == "mysql":
        host, port = mysql_host_and_port()
        status.update(
            {
                "host": host,
                "port": port,
                "database": os.environ.get("VOTERS_DB_NAME"),
            }
        )
        try:
            with voters_db_connect() as db:
                with db.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) AS count FROM `voters`")
                    status["voters_count"] = cursor.fetchone()["count"]
            status["ok"] = True
        except Exception as error:
            status["ok"] = False
            status["error"] = str(error)
        return jsonify(status)

    status.update({"database": str(LOCAL_VOTERS_DATABASE)})
    try:
        with voters_db_connect() as db:
            status["voters_count"] = db.execute("SELECT COUNT(*) FROM voters").fetchone()[0]
        status["ok"] = True
    except Exception as error:
        status["ok"] = False
        status["error"] = str(error)
    return jsonify(status)


@app.route("/api/voters/search")
@login_required
def api_voter_search():
    try:
        query = request.args.get("q", "").strip()
        limit = min(max(int(request.args.get("limit", 50)), 1), 100)
        if len(query) < 2:
            return jsonify({"results": []})

        terms = [term for term in query.split() if term]
        if not terms:
            return jsonify({"results": []})

        fields = [
            "id",
            "uniqueid",
            "first_name",
            "last_name",
            "fathers_name",
            "mothers_name",
            "birthday",
            "age",
            "gender",
            "admin_unit",
            "qv",
            "political_preference",
            "phone_number",
            "job_referrer",
        ]

        if voters_db_driver() == "mysql":
            where = []
            params = []
            for term in terms:
                like = f"%{term}%"
                where.append(
                    "("
                    "`first_name` LIKE %s OR `last_name` LIKE %s OR "
                    "`fathers_name` LIKE %s OR `uniqueid` LIKE %s"
                    ")"
                )
                params.extend([like, like, like, like])
            params.append(limit)
            sql = (
                f"SELECT {', '.join(f'`{field}`' for field in fields)} "
                f"FROM `voters` WHERE {' AND '.join(where)} "
                "ORDER BY `last_name`, `first_name` LIMIT %s"
            )
            with voters_db_connect() as db:
                with db.cursor() as cursor:
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
        else:
            where = []
            params = []
            for term in terms:
                like = f"%{term}%"
                where.append(
                    "("
                    "first_name LIKE ? OR last_name LIKE ? OR "
                    "fathers_name LIKE ? OR uniqueid LIKE ?"
                    ")"
                )
                params.extend([like, like, like, like])
            params.append(limit)
            sql = (
                f"SELECT {', '.join(fields)} FROM voters "
                f"WHERE {' AND '.join(where)} "
                "ORDER BY last_name, first_name LIMIT ?"
            )
            with voters_db_connect() as db:
                rows = [dict(row) for row in db.execute(sql, params).fetchall()]

        return jsonify({"results": rows})
    except Exception as error:
        app.logger.exception("Voter search failed")
        return jsonify({"error": str(error), "results": []}), 500


@app.route("/<page_name>")
@login_required
def page(page_name):
    if page_name not in PAGES:
        return "Page not found", 404

    page_path = BASE_DIR / PAGES[page_name]
    return localize_page(page_path.read_text(encoding="utf-8"), page_name=page_name)


if __name__ == "__main__":
    init_db()
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
        host=os.environ.get("FLASK_HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
    )
