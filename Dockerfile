FROM python:3.10-bullseye

RUN mkdir /app

WORKDIR /app

RUN apt-get update ;\
    apt-get install -y\
      software-properties-common \
      curl \
      make \
      procps \
      vim ;

RUN apt-get update; \
    apt-get install -y ca-certificates curl; \
    install -m 0755 -d /etc/apt/keyrings; \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc; \
    chmod a+r /etc/apt/keyrings/docker.asc;\
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null; \
    apt-get update;\
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

COPY .docker/entrypoint.sh /

COPY . /app

RUN cd /app;\
    pip install .

ENTRYPOINT ["/usr/local/bin/gocker"]
CMD ["--action", "gui"]