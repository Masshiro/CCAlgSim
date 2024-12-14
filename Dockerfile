FROM ubuntu:20.04

# set Non-Interactive Mode
ENV DEBIAN_FRONTEND=noninteractive

RUN ln -fs /usr/share/zoneinfo/America/Vancouver /etc/localtime && \
    echo "America/Vancouver" > /etc/timezone && \
    apt-get update && apt-get install -y \
    sudo \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    mahimahi \
    tzdata \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# install iptables-legacy and conntrack
RUN apt-get update && apt-get install -y iptables conntrack && \
update-alternatives --set iptables /usr/sbin/iptables-legacy && \
update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy


# create non-root user 'ccuser', and set sudo to password-free
RUN useradd -ms /bin/bash ccuser && echo "ccuser:password" | chpasswd \
    && usermod -aG sudo ccuser \
    && echo "ccuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# switch to non-root user
USER ccuser
WORKDIR /home/ccuser

# set working directory
WORKDIR /app

# copy project files into container
COPY . /app

# install python dependencies
RUN python3 -m pip install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]