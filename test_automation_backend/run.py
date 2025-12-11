from app import app

if __name__ == "__main__":
    # Bind to 0.0.0.0 for container environments and use port 5000
    app.run(host="0.0.0.0", port=5000, debug=False)
