.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(LIBYANG)
DERIVED_TARGETS = $(LIBYANG_DEV) $(LIBYANG_DBG) $(LIBYANG_PY2) $(LIBYANG_CPP)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
        # Obtaining the libyang
	rm -fr ./libyang-$(LIBYANG_VERSION)
	git clone https://github.com/CESNET/libyang.git libyang-$(LIBYANG_VERSION)
	pushd libyang-$(LIBYANG_VERSION)
	git checkout -b libyang -f bc8fdee622075db48a16edaa66b0df363346cbe6

	# Apply patch series
	stg init
	stg import -s ../patch/series

	mkdir build
	pushd build
	cmake ..
	make build-deb

	pushd debs
	mv $* $(DEST)/
	mv $(DERIVED_TARGETS) $(DEST)/
	popd

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
