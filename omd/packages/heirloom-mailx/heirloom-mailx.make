HEIRLOOM_MAILX := heirloom-mailx
HEIRLOOM_MAILX_VERS := 12.5
HEIRLOOM_MAILX_DIR := heirloom-mailx-$(HEIRLOOM_MAILX_VERS)

HEIRLOOM_MAILX_BUILD := $(BUILD_HELPER_DIR)/$(HEIRLOOM_MAILX_DIR)-build
HEIRLOOM_MAILX_INSTALL := $(BUILD_HELPER_DIR)/$(HEIRLOOM_MAILX_DIR)-install
HEIRLOOM_MAILX_PATCHING := $(BUILD_HELPER_DIR)/$(HEIRLOOM_MAILX_DIR)-patching

.PHONY: $(HEIRLOOM_MAILX) $(HEIRLOOM_MAILX)-install $(HEIRLOOM_MAILX)-skel $(HEIRLOOM_MAILX)-clean

$(HEIRLOOM_MAILX): $(HEIRLOOM_MAILX_BUILD)

$(HEIRLOOM_MAILX)-install: $(HEIRLOOM_MAILX_INSTALL)

$(HEIRLOOM_MAILX_BUILD): $(HEIRLOOM_MAILX_PATCHING)
	cd $(HEIRLOOM_MAILX_DIR) && $(MAKE) -j 1

$(HEIRLOOM_MAILX_INSTALL): $(HEIRLOOM_MAILX_BUILD)
	mkdir -p $(DESTDIR)$(OMD_ROOT)/bin
	install -m 755 $(HEIRLOOM_MAILX_DIR)/mailx $(DESTDIR)$(OMD_ROOT)/bin/heirloom-mailx
	ln -sfn heirloom-mailx $(DESTDIR)$(OMD_ROOT)/bin/mail
	mkdir -p $(DESTDIR)$(OMD_ROOT)/share/man/man1
	install -m 644 $(HEIRLOOM_MAILX_DIR)/mailx.1 $(DESTDIR)$(OMD_ROOT)/share/man/man1/heirloom-mailx.1
	gzip $(DESTDIR)$(OMD_ROOT)/share/man/man1/heirloom-mailx.1

$(HEIRLOOM_MAILX)-skel:

$(HEIRLOOM_MAILX)-clean:
	rm -rf $(HEIRLOOM_MAILX_DIR) heirloom-mailx $(BUILD_HELPER_DIR)/$(HEIRLOOM_MAILX_DIR)*