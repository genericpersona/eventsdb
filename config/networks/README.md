# Network Configuration

All configuration options for the BaneBot are JSON objects.

BaneBot supports connecting to multiple IRC networks.

Each network's information is stored in a dictionary.

Any instance attributes in twisted.words.protocols.irc.IRCClient can be included.

Some of the supported attributes are:

  - server: hostname or IP address (either IPv4 or IPv6) (string)
 
  - port: port number (integer)
 
  - channels: channels to auto-join (list of strings)
 
  - ssl: whether to use SSL/TLS (bool)
 
  - force_ipv6: whether to force IPv6 name resolution (bool)
 
  - nickname: bot's nickname (string)
 
  - password: bot's password (string or None)
 
  - nickserv_pw: bot's NickServ password (string)
 
  - username: bot's username (string)
 
  - realname: bot's realname (string)
 
  - lineRate: min delay b/w lines (float)
 
   
