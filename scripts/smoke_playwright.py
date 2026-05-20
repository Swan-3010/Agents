def main():
    print("Smoke Playwright script placeholder")

if __name__ == "__main__":
    main()
EOF~ls -R
cat > docker-compose.yml <<'EOF'
services:
  app:
    image: python:3.11-slim
    container_name: receipt-agent-app
    working_dir: /workspace
    env_file:
      - .env
    volumes:
      - ./:/workspace
    command: bash -lc "sleep infinity"
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    container_name: receipt-agent-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
