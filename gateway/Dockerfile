FROM python:3

# disable buffering
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalacja protobuf
RUN apt update && apt install -y jq just
RUN URL=$(curl -s https://api.github.com/repos/protocolbuffers/protobuf/releases/latest | jq -r '.assets[] | select(.name | endswith("linux-x86_64.zip")) | .browser_download_url') && curl -LO $URL && unzip $(basename $URL) -d /usr && rm $(basename $URL)

# justing
COPY justfile .
COPY shared/protobuf shared/protobuf
RUN just generate_protobuf

# Przenoszenie i czyszczenie
RUN mkdir src && mv gateway/src/generated src && rmdir gateway/src gateway

COPY gateway/src ./src/

# CMD [ "sleep", "99999999" ]
CMD [ "python", "-m", "src.main" ]
