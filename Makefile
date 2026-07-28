COMMON_OVERLAYS = tomcat tomcat-apache
COMMON_CONF = tomcat

include $(FAB_PATH)/common/mk/turnkey/mysql.mk
include $(FAB_PATH)/common/mk/turnkey/apache.mk
include $(FAB_PATH)/common/mk/turnkey/tkl-webcp.mk
include $(FAB_PATH)/common/mk/turnkey.mk
