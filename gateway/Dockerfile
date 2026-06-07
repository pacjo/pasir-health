FROM python:3

# disable buffering
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalacja protobuf
RUN apt update && apt install -y jq && apt install just
RUN URL=$(curl -s https://api.github.com/repos/protocolbuffers/protobuf/releases/latest | jq -r '.assets[] | select(.name | endswith("linux-x86_64.zip")) | .browser_download_url')
RUN curl -LO $URL && unzip $(basename $URL) -d $HOME/.local && export PATH="$PATH:$HOME/.local/bin"

# justing
RUN just generate_protobuf

COPY src ./src/

CMD [ "python", "-m", "src.main" ]
