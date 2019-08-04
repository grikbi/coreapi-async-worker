FROM registry.centos.org/centos/centos:7

ENV F8A_WORKER_VERSION=d403113 \
    F8A_UTIL_VERSION=de8046b \
    LC_ALL=en_US.utf-8 \
    LANG=en_US.utf-8

RUN yum install -y epel-release &&\
    yum install -y gcc git python36-pip python36-requests httpd httpd-devel python36-devel &&\
    yum clean all

COPY ./requirements.txt /

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt && rm requirements.txt
RUN pip3 install git+https://github.com/fabric8-analytics/fabric8-analytics-worker.git@${F8A_WORKER_VERSION}
RUN pip3 install git+https://github.com/fabric8-analytics/fabric8-analytics-utils.git@${F8A_UTIL_VERSION}
RUN pip3 install git+https://git@github.com/fabric8-analytics/fabric8-analytics-version-comparator.git#egg=f8a_version_comparator

COPY ./src /src

ADD scripts/entrypoint.sh /bin/entrypoint.sh

RUN chmod +x /bin/entrypoint.sh

ENTRYPOINT ["/bin/entrypoint.sh"]
