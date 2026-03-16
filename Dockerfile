FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
  python3 \
  python3-pip \
  git \
  locales \
  fontconfig \
  texlive \
  texlive-luatex \
  texlive-plain-generic \
  texlive-lang-czechslovak \
  texlive-fonts-recommended \
  poppler-utils \
  psutils \
  ghostscript \
  && rm -rf /var/lib/apt/lists/*

RUN locale-gen cs_CZ.UTF-8 && update-locale LANG=cs_CZ.UTF-8
ENV LANG=cs_CZ.UTF-8
ENV LC_ALL=cs_CZ.UTF-8

WORKDIR /songbook

COPY . .

# Install Scout fonts (TheMix C5, SKAUT) from fonts/ directory
COPY fonts/ /usr/local/share/fonts/custom/
RUN fc-cache -fv && luaotfload-tool --update

ENTRYPOINT ["python3", "build_songbook.py"]
