NAME			:=	propelleride
TITLE			:=	PropellerIDE

DIR				:=	$(shell pwd)
DIR_SRC			:=	$(DIR)/src
DIR_BUILD		:=	$(DIR)/build

DIR_STAGING		:=	$(DIR)/staging
DIR_OUT			:=	$(DIR_STAGING)

DIR_DIST		:=	$(DIR)/dist

DIR_COMMON		:=	$(DIR)/common

ISCC			:=	iscc
QMAKE_OPTS		+=  -r
QMAKE			:=	qmake $(QMAKE_OPTS)

XML				:=	$(DIR)/repo.xml
REPO			:=	$(DIR_DIST)/repo.py $(XML)

VERSION 		:=	$(shell $(REPO) -v)

ifeq ($(shell uname -m),i686)			# if i686
	CPU := i386
else ifeq ($(shell uname -m),x86_64)	# if x64
	CPU := amd64
else
	CPU := $(shell uname -m)
endif

all: build

help:
	@echo "Usage:    make [TYPE]"
	@echo
	@echo "Enter package type to build. Options:"
	@echo "    checkout     initialize child repositories"
	@echo
	@echo "    win    		windows installer"
	@echo "    mac    		mac bundle"
	@echo "    deb    		debian package"
	@echo "    rpi    		debian package for Raspberry Pi"
	@echo
	@echo "No parameter builds only the binaries"


checkout:
	$(REPO)

build:
	cd $(DIR_SRC); $(QMAKE) CPU=$(CPU) VERSION_ARG=$(VERSION) PREFIX=$(DIR_OUT); $(MAKE)

copy: build
	cd $(DIR_SRC); $(MAKE) install

clean_staging:
	rm -rf $(DIR_STAGING)

clean: clean_staging
	cd $(DIR_SRC); $(QMAKE); $(MAKE) clean

distclean: clean_staging
	cd $(DIR_SRC); $(QMAKE); $(MAKE) distclean

archive:
	mkdir -p $(DIR_STAGING)
	$(REPO) --archive $(DIR_STAGING)/$(NAME)-$(VERSION).tgz

deb: DIR_OUT := $(DIR_STAGING)/$(NAME)/usr
deb: DIR_DEBIAN := $(DIR_STAGING)/$(NAME)/DEBIAN
deb: DIR_MAN := $(DIR_OUT)/share/man/man1/
deb: clean_staging copy
	mkdir -p $(DIR_MAN)
	for f in $(DIR_OUT)/share/$(NAME)/bin/* ; \
		do \
			echo $$f ; \
			help2man --no-info $$f > $(DIR_MAN)/`basename $$f`.1 ; \
			gzip $(DIR_MAN)/`basename $$f`.1 ; \
	   	done
	mkdir -p $(DIR_DEBIAN)
	cp -f $(shell ldd $(DIR_OUT)/bin/$(NAME) \
		| grep "libQt" \
		| awk '{print $$3}') $(DIR_OUT)/share/$(NAME)/bin/
	$(DIR_DIST)/debian.py --arch $(CPU) --out $(DIR_DEBIAN)/control  $(XML)
	echo 9 > $(DIR_DEBIAN)/compat
	dpkg-deb -b $(DIR_STAGING)/$(NAME) $(DIR_STAGING)/$(NAME)-$(VERSION)-$(CPU).deb

rpi: CPU := armhf
rpi: deb

win: DIR_OUT := "$(DIR_STAGING)/$(NAME)"
win: clean_staging copy
	cd $(DIR_OUT); \
	windeployqt $(NAME).exe; \
	$(DIR_DIST)/iss.py $(XML) -s | $(ISCC) -


mac: DIR_OUT := "$(DIR_STAGING)/$(NAME).app/Contents"
mac: clean_staging copy
	cd $(DIR_STAGING) ; \
	macdeployqt $(DIR_STAGING)/$(TITLE).app ; \
	$(DIR_DIST)/plist.py $(XML) -o $(DIR_OUT)/Info.plist ; \
	$(DIR_DIST)/dmg.sh \
			$(DIR_STAGING)/$(TITLE).app \
			$(TITLE) \
			$(DIR_STAGING)/$(NAME)-$(VERSION)-$(CPU).dmg \
			$(shell $(REPO) --gfx)/mac-dmg.png
