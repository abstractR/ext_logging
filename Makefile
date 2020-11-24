RELEASE ?= 1
RPMDIR=$(shell rpm --eval %{_rpmdir})

OS_VERSION  := 7
GROUP ?=com.example
BUILDARCH=noarch
PKGNAME=ops-logging
PYTHONS=python2.6 python2.7 python3.4 python3.6
VERSION:=$(or $(VERSION),dev)

SITE_python3.6 := /usr/lib/python3.6/site-packages

SITE_python3.4 := /usr/lib/python3.4/site-packages
# python from IUS
SITE_python2.7 := /usr/lib/python2.7/site-packages
# standard el6
SITE_python2.6 := /usr/lib/python2.6/site-packages

PACKAGE_python3.6 := python36

#package names
PACKAGE_python3.4 := python34
# python from IUS
PACKAGE_python2.7 := python27
# standard el6
PACKAGE_python2.6 := python

all: $(PYTHONS)

$(PYTHONS): clean
	rpmbuild -bb --define "name $(PKGNAME)-$(@)" --define "_curdir `pwd`" --define "version $(VERSION)" --define "os_version 7"  \
	--define "site $(SITE_$(@))" --define "python_package $(PACKAGE_$(@))" --define "python_version $(@)" $(PKGNAME).spec

# Upload RPMs for all os versions to Sonatype Nexus
# Requires package repository-tools
uploadrpms: $(PYTHONS)
	$(foreach python_version, $(PYTHONS), \
		artifact upload  --staging --use-direct-put --artifact $(PKGNAME)-$(python_version) --version $(VERSION)-$(RELEASE) \
		$(RPMDIR)/$(BUILDARCH)/$(PKGNAME)-$(python_version)-$(VERSION)-*$(BUILDARCH).rpm \
		rpms-opstools-el6  $(GROUP); \
	)

# python from software collections
#SITE_python2.7 := /opt/rh/python27/root/usr/lib/python2.7/site-packages

clean:
	rm -fr $(RPMDIR)/*
