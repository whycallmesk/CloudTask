"""CloudTask - a scalable task manager deployed on AWS.

Stack: Flask + Gunicorn on EC2 (Auto Scaling Group behind an ALB),
Amazon RDS (MySQL) for data, Amazon S3 for file attachments.
Configuration comes from environment variables (set by CloudFormation UserData).
"""
import os
import socket
import threading
import time
import uuid

import boto3
import pymysql
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "cloudtask")
BUCKET = os.environ.get("S3_BUCKET", "")
REGION = os.environ.get("AWS_REGION", "us-east-1")

s3 = boto3.client("s3", region_name=REGION) if BUCKET else None


def get_conn():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=3,
    )


def init_db():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE,
                attachment_key VARCHAR(512) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
    conn.close()


def attachment_url(key):
    if not key or not s3:
        return None
    return s3.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": key}, ExpiresIn=300
    )


@app.route("/")
def index():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        tasks = cur.fetchall()
    conn.close()
    for t in tasks:
        t["url"] = attachment_url(t["attachment_key"])
    # Hostname shows which EC2 instance served the request (proves load balancing)
    return render_template("index.html", tasks=tasks, instance=socket.gethostname())


@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    if not title:
        return redirect(url_for("index"))
    key = None
    f = request.files.get("file")
    if f and f.filename and s3:
        key = f"attachments/{uuid.uuid4()}-{os.path.basename(f.filename)}"
        s3.upload_fileobj(f, BUCKET, key)
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO tasks (title, attachment_key) VALUES (%s, %s)", (title, key)
        )
    conn.close()
    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle(task_id):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("UPDATE tasks SET done = NOT done WHERE id = %s", (task_id,))
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.close()
    return redirect(url_for("index"))


@app.route("/health")
def health():
    """Used by the ALB target group health check (does not touch the DB)."""
    return jsonify(status="ok", instance=socket.gethostname())


@app.route("/cpu")
def cpu():
    """Burns CPU for ~1s. Used by load_test.sh to trigger auto scaling in the demo."""
    x = 0
    for i in range(8_000_000):
        x += i * i
    return jsonify(done=True, instance=socket.gethostname())


# RDS can take a little longer to accept connections after CloudFormation
# creates it. Initialize the schema on the first application request (but not
# on the ALB health-check endpoint), retrying briefly if the database is not
# ready yet. Each Gunicorn worker initializes its own process-local flag.
_schema_ready = False
_schema_lock = threading.Lock()


def ensure_schema():
    global _schema_ready
    if _schema_ready:
        return

    with _schema_lock:
        if _schema_ready:
            return
        last_error = None
        for attempt in range(6):
            try:
                init_db()
                _schema_ready = True
                app.logger.info("CloudTask database schema is ready")
                return
            except Exception as exc:
                last_error = exc
                app.logger.warning(
                    "Database not ready (attempt %s/6): %s", attempt + 1, exc
                )
                if attempt < 5:
                    time.sleep(2)
        raise RuntimeError("Could not initialize the CloudTask database") from last_error


@app.before_request
def initialize_database_for_application_requests():
    # Keep ALB health checks independent of database startup.
    if request.path != "/health":
        ensure_schema()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
