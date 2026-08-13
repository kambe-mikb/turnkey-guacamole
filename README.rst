Apache Guacamole - a Clientless Remote Desktop Gateway
======================================================

`Guacamole`_  is an HTML5 web application that provides access to desktop
environments using remote desktop protocols (such as VNC or RDP). It provides
cross-browser mouse and keyboard events, an XML-driven on-screen keyboard, and
synchronized nestable layers with hardware-accelerated compositing.

Guacamole allows access one or more desktops from anywhere remotely, without
requiring the installation of special clients, making it particularly useful when
installing a client is not possible. By setting up a Guacamole server, you can
provide access to any other computer on the network from virtually any other
computer on the internet, anywhere in the world. Even mobile phones or tablets
can be used, without having to install anything.

Guacamole is specifically designed to not care whether you have a mouse,
keyboard, touchscreen, or any combination of those.

One of the major design philosophies behind Guacamole is that it should never
assume you have a particular device just because your browser has or is missing
a specific feature. Guacamole's code base provides support for both mouse and
touch events simultaneously, without choosing one over the other, while the
interface is intended to be usable regardless of screen size.

Guacamole is implemented as a JAVA servlet running within Apache `Tomcat`_ (as
the servlet container). This appliance provides a standalone Guacamole server
running in Tomcat, integrated with the Apache web server. It uses MySQL as its
backing database.

This appliance includes all the standard features in `TurnKey Core`_,
and on top of that:

- Guacamole Server:
   - The default Apache index file (/var/www/index.html) uses javascript to
     redirect the root web page to the guacamole server.
   - The LDAP Authentication extension is installed.
   - The OpenId SSO Authentication externsion is installed.
   - The Session Recording Storage extension is installed.
   - A firstboot utility allows the creation of an initial user account to
     access guacamole from the web.
     
- Tomcat on Apache configurations:
   
   - TurnKey web control panel in /var/lib/tomcat10/webapps/cp
   - All components installed from package management.
   - Using OpenJDK Java runtime.
   - Deployed web applications in /var/lib/tomcat10/webapps.
   - TurnKey web control panel in /var/lib/tomcat10/webapps/cp.
   - JSP console output sent to syslog (/var/log/syslog).
   - Created Tomcat admin/manager roles and admin user.
   - Use Apache2 Jk loadbalancer connector (performance).
   - JkMounts for admin, manager, host-manager applications
     (convenience).
   - Bind Tomcat AJP connector to localhost (security).
   - Removed Tomcat HTTP connector listener (security).
   - Set system wide Tomcat and Java environment variables.

- Includes MySQL.
- SSL support out of the box.
- Includes Webmin module for configuring Apache2 and MySQL.

See the `TurnKey Guacamole docs`_ for further details.

Credentials *(passwords set at first boot)*
-------------------------------------------

-  Webmin, SSH, MySQL: username **root**
-  Tomcat administration applications: username **admin**
-  Guacamole process owner and database owner: username **guacadmin**

.. _Guacamole: https://guacamole.apache.org
.. _Tomcat: https://tomcat.apache.org
.. _TurnKey Core: https://www.turnkeylinux.org/core
.. _TurnKey Guacamole docs: https://github.com/kambe-mikb/guacamole/docs/
