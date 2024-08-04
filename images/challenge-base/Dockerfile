FROM python:3.12

ENV PORT=31337

RUN mkdir /var/log/ctf /startup
RUN apt update
RUN apt install -y tini
RUN rm -rf /var/cache/apt/archives
RUN useradd --shell /bin/bash -m ctf

COPY requirements.txt /root
RUN python3 -m pip install --default-timeout=9999 -r /root/requirements.txt

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# RUN dos2unix /entrypoint.sh
# RUN dos2unix /startup/00-create-xinetd-service
# RUN dos2unix /startup/99-start-xinetd
# RUN dos2unix /home/ctf/handler.sh

ENTRYPOINT ["tini", "-g", "--"]
CMD ["bash", "/entrypoint.sh"]
