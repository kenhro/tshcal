# just a placeholder for now to see something here...

import socket

Int32Bit = 214748300

Int16Bit = 400

# Convert a 32 bit integer from network byte order to host byte order

Int32InHostFormat = socket.ntohl(Int32Bit)

# Convert a 16 bit integer from network byte order to host byte order

Int16InHostFormat = socket.ntohs(Int16Bit)

print("32 bit integer {} converted from Network Byte Order to Host Byte Order: {}".format(Int32Bit, Int32InHostFormat))

print("16 bit integer {} converted from Network Byte Order to Host Byte Order: {}".format(Int16Bit, Int16InHostFormat))

# Convert a 32 bit integer from host byte order to network byte order

Int32InNetworkFormat = socket.htonl(Int32InHostFormat)

# Convert a 16 bit integer from network byte order to host byte order

Int16InNetworkFormat = socket.htons(Int16InHostFormat)

print("32 bit integer {} converted from Host Byte Order to Network Byte Order: {}".format(Int32InHostFormat,
                                                                                          Int32InNetworkFormat))

print("16 bit integer {} converted from Host Byte Order to Network Byte Order: {}".format(Int16InHostFormat,
                                                                                          Int16InNetworkFormat))