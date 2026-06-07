FROM python:3

# disable buffering
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalacja protobuf
RUN apt update && apt install -y jq
RUN URL=$(curl -s https://api.github.com/repos/protocolbuffers/protobuf/releases/latest | jq -r '.assets[] | select(.name | endswith("linux-x86_64.zip")) | .browser_download_url')
RUN curl -LO $URL && unzip $(basename $URL) -d $HOME/.local && export PATH="$PATH:$HOME/.local/bin"

# RUN protoc -I=src --python_out=src src/protobuf/activity_message.proto
# RUN protoc -I=src --python_out=src src/protobuf/alert_message.proto
# RUN protoc -I=src --python_out=src src/protobuf/heartbeat_message.proto
# RUN protoc -I=src --python_out=src src/protobuf/idle_message.proto
# RUN protoc -I=src --python_out=src src/protobuf/sleep_message.proto

COPY src ./src/

CMD [ "python", "-m", "src.main" ]
