#!/bin/bash
./vpnclient start
./vpncmd /CLIENT localhost /CMD AccountConnect casavpn
dhclient vpn_casavpn
ip route del default via 10.20.254.254
ip route add default via 192.168.30.1
ip route add 10.40.90.101 via 10.20.254.254
