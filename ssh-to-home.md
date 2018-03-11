# SSH + Wake-on-LAN for home desktop

I want to access my home desktop from the Internet. The two main issues are:

1. I don't have a static IP.
2. My desktop idles at 75W of power which is wasteful.

Hence, the following setup for SSH and Wake-on-LAN with dynamic DNS.

## SSH setup

1. Install and run SSH server (`sudo apt install openssh-server`) on desktop
2. Copy public keys from target computers (`ssh-copy-id` or USB-stick) to desktop
3. Disable password authentication on desktop: In `/etc/ssh/sshd_config`,
   uncomment and modify the pertinent line to `PasswordAuthentication no`
4. Restart ssh daemon: `sudo service ssh restart`
5. You should be able to ssh in at this point.

## Wake-on-LAN (WOL) setup on desktop

1. In BIOS, enable WOL (it may be listed as power-up by PCI-E)
2. In Linux, make sure WOL is enabled: `sudo ethtool <eth>`. It should say:
   `Wake-on: g`. If not, set it with `sudo ethtool -s <eth> wol g` and make it
   [persistent](https://wiki.archlinux.org/index.php/Wake-on-LAN#cron).
3. You should be able to wake the desktop up from another computer on the same
   LAN: `sudo apt install wakeonlan; wakeonlan <MAC-addr>`. Get the MAC address
   of the desktop's ethernet device with `ifconfig`.

## Access from outside world

1. Give a static IP address to the desktop in the router.
2. Forward TCP port 22 for SSH and UDP port 9 for WOL from the internet to the desktop.
3. Get a [dynamic DNS](https://duckdns.org). My router can send updates to the
   service, or you have some other device on your LAN (a Raspberry Pi, for
   example) send updates.
4. Now, you should be able to `wakeonlan -i subdomain.duckdns.org <MAC-addr>`
   and then, `ssh subdomain.duckdns.org`.

## Router issues

It turns out that my router forgets the MAC address of the desktop some time
after the desktop has been shut down (ARP caches typically hold entries for 30
seconds only.) This is in spite of the fact that the router assigns a static IP
to the desktop based on its MAC address. The upshot of this is that the router
can forward WOL requests to the desktop only when the desktop is running (and
about 30 seconds after it has been shut down.)

One solution is to forward UDP port 9 to the broadcast IP on the LAN, but my
router does not allow that.

Hence, I use an always-on Beaglebone Black (BBB) on the LAN to send the WOL. I
start an SSH server on the BBB and forward it to the internet on port 9022. Now
I can do:

```
ssh -p 9022 subdomain.duckdns.org wakeonlan <MAC-addr>
# wait for desktop to wake up
ssh subdomain.duckdns.org
```

This has the benefit that the WOL request is authenticated. As on the desktop,
use appropriate security on the BBB (disabling password authentication, for
example.)
