#!/bin/bash

KEYS_DIR=.
set -e 
set -x

if ! test -f /usr/share/openvpn/easy-rsa/2.0/vars  ; then
    echo "Error: missing easy-rsa scripts"
    exit 1
fi

cd /etc/openvpn
. /usr/share/openvpn/easy-rsa/2.0/vars 

export KEY_PROVINCE="CA"
export KEY_CITY="SanFrancisco"
export KEY_ORG="M-Lab"
export KEY_EMAIL=support@measurementlab.net
export KEY_CN=`hostname`
export KEY_NAME=`hostname`
export KEY_OU=M-Lab-Ops

# TODO: set more suitable values here.
export PKCS11_MODULE_PATH=changeme
export PKCS11_PIN=1234

cat <<EOF >ca.crt
-----BEGIN CERTIFICATE-----
MIIDGTCCAoKgAwIBAgIJAM+qaqjZwWxHMA0GCSqGSIb3DQEBBQUAMGcxCzAJBgNV
BAYTAlVTMQswCQYDVQQIEwJDQTEVMBMGA1UEBxMMU2FuRnJhbmNpc2NvMQ4wDAYD
VQQKEwVNLUxhYjEkMCIGA1UEAxMbdnBuLXRlc3QubWVhc3VyZW1lbnRsYWIubmV0
MB4XDTEzMDMwNTE4MDUwOFoXDTIzMDMwMzE4MDUwOFowZzELMAkGA1UEBhMCVVMx
CzAJBgNVBAgTAkNBMRUwEwYDVQQHEwxTYW5GcmFuY2lzY28xDjAMBgNVBAoTBU0t
TGFiMSQwIgYDVQQDExt2cG4tdGVzdC5tZWFzdXJlbWVudGxhYi5uZXQwgZ8wDQYJ
KoZIhvcNAQEBBQADgY0AMIGJAoGBALDtuqRaqUxIGHbbp9caCMWjrDK+DiRqbZ2k
uH7FG5lYcnjr0QlYS3bmo8qrwOUrQrnWHcXZ7gJtHKT/G06ASEIL/OxpchfBgh12
PhyYA1X48WLE5zFUu1GVZy62Oa2HEBGMvx2Xav4iKdU79k6MZf1ZcTbDq8YKBKwU
qRwX1oOBAgMBAAGjgcwwgckwHQYDVR0OBBYEFMsrwVEPZtJEkT3nt9tdD27xTHZL
MIGZBgNVHSMEgZEwgY6AFMsrwVEPZtJEkT3nt9tdD27xTHZLoWukaTBnMQswCQYD
VQQGEwJVUzELMAkGA1UECBMCQ0ExFTATBgNVBAcTDFNhbkZyYW5jaXNjbzEOMAwG
A1UEChMFTS1MYWIxJDAiBgNVBAMTG3Zwbi10ZXN0Lm1lYXN1cmVtZW50bGFiLm5l
dIIJAM+qaqjZwWxHMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQADgYEAYaT/
gLdg/5QxSGpv6QNmrzmed+xc6c8VSALEUtzxTYj+N7wBkorVzyFUDW+H5XHt7PXd
OEg3N8QRwfC9vIssYm4D9FDB4GgOa0Unfz0YvAaguP8pLF3bq8hbHwmOb4YqxYLV
veW13ZpmuKlAkRJCu/647KLeP428KnhPuqdugbg=
-----END CERTIFICATE-----
EOF

# TODO: check output
if ! test -f client.key || ! test -f client.csr ; then
    openssl req -batch -days 3650 -nodes -new -newkey rsa:1024 -keyout client.key \
        -out client.csr -config /usr/share/openvpn/easy-rsa/2.0/openssl-1.0.0.cnf
fi

# TODO: check for errors
# TODO: use https and certificates, to identify VPN server
if ! test -f client.crt ; then
    curl --data-urlencode "csr=`cat client.csr`" \
         --data-urlencode "session=`cat /etc/planetlab/session`" \
         http://vpn-test.measurementlab.net/sign-csr.php >client.crt
fi

# NOTE: check that the cert looks legitimate
if ! grep -q "BEGIN CERTIFICATE" client.crt ; then
  echo Certificate could not be received correctly >&2
  exit 1
fi

# NOTE: default configuration
cat <<EOF >/etc/openvpn/client.conf
##############################################
# Sample client-side OpenVPN 2.0 config file #
# for connecting to multi-client server.     #
#                                            #
# This configuration can be used by multiple #
# clients, however each client should have   #
# its own cert and key files.                #
#                                            #
# On Windows, you might want to rename this  #
# file so it has a .ovpn extension           #
##############################################

# Specify that we are a client and that we
# will be pulling certain config file directives
# from the server.
client

# Use the same setting as you are using on
# the server.
# On most systems, the VPN will not function
# unless you partially or fully disable
# the firewall for the TUN/TAP interface.
dev tun

# Are we connecting to a TCP or
# UDP server?  Use the same setting as
# on the server.
proto udp

# The hostname/IP and port of the server.
# You can have multiple remote entries
# to load balance between the servers.
remote vpn-test.measurementlab.net 1194

# Keep trying indefinitely to resolve the
# host name of the OpenVPN server.  Very useful
# on machines which are not permanently connected
# to the internet such as laptops.
resolv-retry infinite

# Most clients don't need to bind to
# a specific local port number.
nobind

# TODO: identify if this will work on M-lab
# Downgrade privileges after initialization (non-Windows only)
;user nobody
;group nobody

# Try to preserve some state across restarts.
persist-key
persist-tun

# SSL/TLS parms.
# See the server config file for more
# description.  It's best to use
# a separate .crt/.key file pair
# for each client.  A single ca
# file can be used for all clients.
ca   /etc/openvpn/ca.crt
cert /etc/openvpn/client.crt
key  /etc/openvpn/client.key

# Verify server certificate by checking
# that the certicate has the nsCertType
# field set to "server".  This is an
# important precaution to protect against
# a potential attack discussed here:
#  http://openvpn.net/howto.html#mitm
#
# To use this feature, you will need to generate
# your server certificates with the nsCertType
# field set to "server".  The build-key-server
# script in the easy-rsa folder will do this.
ns-cert-type server

# If a tls-auth key is used on the server
# then every client must also have the key.
;tls-auth ta.key 1

# Enable compression on the VPN link.
# Don't enable this unless it is also
# enabled in the server config file.
comp-lzo

# Set log file verbosity.
verb 3

EOF
 
chkconfig --level 345 openvpn on
#service openvpn start

