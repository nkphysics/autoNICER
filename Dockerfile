FROM ubuntu:20.04

ARG version=6.31.1
ENV HEASOFT_VERSION=${version}

LABEL version="${version}" \
      description="HEASoft ${version} https://heasarc.gsfc.nasa.gov/lheasoft/" \
      maintainer="NASA/GSFC/HEASARC https://heasarc.gsfc.nasa.gov/cgi-bin/ftoolshelp"

# Install HEASoft prerequisites
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get -y upgrade \
 && apt-get -y install \
    libreadline-dev \
    libncurses5-dev \
    ncurses-dev \
    curl \
    libcurl4 \
    libcurl4-gnutls-dev \
    xorg-dev \
    make \
	gcc \
	gfortran \
	g++ \
	perl-modules \
	libwww-perl \
	python3-dev \
	python3-pip \
	python3-setuptools \
	python3-venv \
	python-is-python3 \
	tcsh \
	wget \
 && pip3 install numpy \
    scipy \
    astropy \
    autonicer \
 && apt-get clean

RUN groupadd heasoft && useradd -r -m -g heasoft heasoft \
 && mkdir -p /opt/heasoft/caldb \
 && mkdir -p /opt/heasoft/geomag \
 && chown -R heasoft:heasoft /opt/heasoft

USER heasoft
WORKDIR /home/heasoft

# Retrieve the HEASoft source code, unpack, configure,
# make, install, clean up, and create symlinks....
ARG heasoft_tarfile_suffix=src
RUN wget https://heasarc.gsfc.nasa.gov/FTP/software/lheasoft/lheasoft${HEASOFT_VERSION}/heasoft-${HEASOFT_VERSION}${heasoft_tarfile_suffix}.tar.gz \
 && echo "Unpacking heasoft-${HEASOFT_VERSION}${heasoft_tarfile_suffix}.tar.gz..." \
 && tar xzvf heasoft-${HEASOFT_VERSION}${heasoft_tarfile_suffix}.tar.gz \
 && rm -f heasoft-${HEASOFT_VERSION}${heasoft_tarfile_suffix}.tar.gz \
 && cd ${HOME}/heasoft-${HEASOFT_VERSION}/BUILD_DIR/ \
 && ./configure --prefix=/opt/heasoft 2>&1 | tee ${HOME}/configure.log \
 && make 2>&1 | tee ${HOME}/build.log \
 && make install 2>&1 | tee ${HOME}/install.log \
 && make clean 2>&1 \
 && /bin/bash -c 'cd /opt/heasoft/; for loop in x86_64*/*; do ln -sf $loop; done' \
 && cd ${HOME}/heasoft-${HEASOFT_VERSION} \
 && cp -p Xspec/BUILD_DIR/hmakerc /opt/heasoft/bin/ \
 && cp -p Xspec/BUILD_DIR/Makefile-std /opt/heasoft/bin/ \
 && rm -rf Xspec/src/spectral \
 && cd \
 && gzip -9 ${HOME}/*.log \
 && cp -p ${HOME}/heasoft-${HEASOFT_VERSION}/Release_Notes* /opt/heasoft/
 # && mkdir ${HOME}/heasoft-${HEASOFT_VERSION}/geomag

# Configure shells...
RUN /bin/echo >> /home/heasoft/.bashrc \
 && /bin/echo '# Initialize HEASoft environment' >> /home/heasoft/.bashrc \
 && /bin/echo 'export HEADAS=/opt/heasoft' >> /home/heasoft/.bashrc \
 && /bin/echo '. $HEADAS/headas-init.sh' >> /home/heasoft/.bashrc \
 && /bin/echo >> /home/heasoft/.bashrc \
 && /bin/echo '# Initialize environment for CALDB' >> /home/heasoft/.bashrc \
 && /bin/echo 'export CALDB=https://heasarc.gsfc.nasa.gov/FTP/caldb' >> /home/heasoft/.bashrc \
 && /bin/echo 'export CALDBCONFIG=/opt/heasoft/caldb/caldb.config' >> /home/heasoft/.bashrc \
 && /bin/echo 'export CALDBALIAS=/opt/heasoft/caldb/alias_config.fits' >> /home/heasoft/.bashrc \
 && /bin/echo >> /home/heasoft/.profile \
 && /bin/echo '# Initialize HEASoft environment' >> /home/heasoft/.profile \
 && /bin/echo 'export HEADAS=/opt/heasoft' >> /home/heasoft/.profile \
 && /bin/echo '. $HEADAS/headas-init.sh' >> /home/heasoft/.profile \
 && /bin/echo >> /home/heasoft/.profile \
 && /bin/echo '# Initialize environment for CALDB' >> /home/heasoft/.profile \
 && /bin/echo 'export CALDB=https://heasarc.gsfc.nasa.gov/FTP/caldb' >> /home/heasoft/.profile \
 && /bin/echo 'export CALDBCONFIG=/opt/heasoft/caldb/caldb.config' >> /home/heasoft/.profile \
 && /bin/echo 'export CALDBALIAS=/opt/heasoft/caldb/alias_config.fits' >> /home/heasoft/.profile \
 && /bin/echo '# Initialize HEASoft environment' >> /home/heasoft/.cshrc \
 && /bin/echo 'setenv HEADAS /opt/heasoft' >> /home/heasoft/.cshrc \
 && /bin/echo 'source $HEADAS/headas-init.csh' >> /home/heasoft/.cshrc \
 && /bin/echo >> /home/heasoft/.cshrc \
 && /bin/echo '# Initialize environment for CALDB' >> /home/heasoft/.cshrc \
 && /bin/echo 'setenv CALDB https://heasarc.gsfc.nasa.gov/FTP/caldb' >> /home/heasoft/.cshrc \
 && /bin/echo 'setenv CALDBCONFIG /opt/heasoft/caldb/caldb.config' >> /home/heasoft/.cshrc \
 && /bin/echo 'setenv CALDBALIAS /opt/heasoft/caldb/alias_config.fits' >> /home/heasoft/.cshrc \
 && /bin/echo >> /home/heasoft/.bashrc \
 && /bin/echo '# Setup GEOMAG data Path' >> /home/heasoft/.bashrc \
 && /bin/echo 'export GEOMAG_PATH=/opt/heasoft/geomag' >> /home/heasoft/.bashrc \
 && /bin/echo >> /home/heasoft/.profile \
 && /bin/echo '# Setup GEOMAG data Path' >> /home/heasoft/.profile \
 && /bin/echo 'export GEOMAG_PATH=/opt/heasoft/geomag' >> /home/heasoft/.profile \
 && /bin/echo >> /home/heasoft/.cshrc \
 && /bin/echo '# Setup GEOMAG data Path' >> /home/heasoft/.cshrc \
 && /bin/echo 'setenv GEOMAG_PATH=/opt/heasoft/geomag' >> /home/heasoft/.cshrc
 

RUN cd /opt/heasoft/caldb \
    && wget https://heasarc.gsfc.nasa.gov/FTP/caldb/software/tools/caldb.config \
    && wget https://heasarc.gsfc.nasa.gov/FTP/caldb/software/tools/alias_config.fits

ENV CC=/usr/bin/gcc \
    CXX=/usr/bin/g++ \
    FC=/usr/bin/gfortran \
    PERL=/usr/bin/perl \
    PERLLIB=/opt/heasoft/lib/perl \
    PERL5LIB=/opt/heasoft/lib/perl \
    PYTHON=/usr/bin/python \
    PYTHONPATH=/opt/heasoft/lib/python:/opt/heasoft/lib \
    PATH=/opt/heasoft/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    HEADAS=/opt/heasoft \
    LHEASOFT=/opt/heasoft \
    FTOOLS=/opt/heasoft \
    LD_LIBRARY_PATH=/opt/heasoft/lib \
    LHEAPERL=/usr/bin/perl \
    PFCLOBBER=1 \
    PFILES=/home/heasoft/pfiles;/opt/heasoft/syspfiles \
    FTOOLSINPUT=stdin \
    FTOOLSOUTPUT=stdout \
    LHEA_DATA=/opt/heasoft/refdata \
    LHEA_HELP=/opt/heasoft/help \
    EXT=lnx \
    PGPLOT_FONT=/opt/heasoft/lib/grfont.dat \
    PGPLOT_RGB=/opt/heasoft/lib/rgb.txt \
    PGPLOT_DIR=/opt/heasoft/lib \
    POW_LIBRARY=/opt/heasoft/lib/pow \
    XRDEFAULTS=/opt/heasoft/xrdefaults \
    TCLRL_LIBDIR=/opt/heasoft/lib \
    XANADU=/opt/heasoft \
    XANBIN=/opt/heasoft \
    CALDB=https://heasarc.gsfc.nasa.gov/FTP/caldb \
    CALDBCONFIG=/opt/heasoft/caldb/caldb.config \
    CALDBALIAS=/opt/heasoft/caldb/alias_config.fits \
    GEOMAG_PATH=/opt/heasoft/geomag 

CMD [ "fversion" ]
