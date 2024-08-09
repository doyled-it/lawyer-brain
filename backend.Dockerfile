FROM python:3.12-slim

# Set the working directory
WORKDIR /app

ENV PATH="/root/.local/bin:${PATH}"

# Copy the current directory contents into the container at /app
RUN apt update -y && \
    apt install -y pipx && \
    pipx install poetry && \
    pipx ensurepath && \
    export PATH=$PATH:$HOME/.local/bin

RUN /root/.local/bin/poetry --version

COPY pyproject.toml poetry.lock README.md /app/
COPY lb /app/lb

# Install any needed packages specified in requirements.txt
RUN /root/.local/bin/poetry install --without dev

CMD /root/.local/bin/poetry run uvicorn lb.api.api:app --host 0.0.0.0 --port ${PORT}
