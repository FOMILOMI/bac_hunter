import uvicorn

if __name__ == "__main__":
	uvicorn.run("webapp.backend:app", host="0.0.0.0", port=9000, reload=False)