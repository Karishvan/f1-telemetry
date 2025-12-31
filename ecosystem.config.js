module.exports = {
  apps: [{
    name: "f1-api",
    script: "venv/bin/uvicorn",
    args: "main:app --host 0.0.0.0 --port 8000",
    interpreter: "python3",
    env: {
      NODE_ENV: "production",
    }
  }]
}

