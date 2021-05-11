# sauter_logger

A simple data logger example program
for [Sauter SU 130](https://www.sauter.eu/shop/en/measuring-instruments/occupational-safety-environment/SU/) (and maybe others).
The 2.5mm jack is RS232 (I measured around 3.7V from the device) and the [cable](https://www.sauter.eu/shop/de/zubehoer/software/ATC-01/) I got already contains a PL2303. The software which comes with the cable works but only runs in Windows. I wasn't able to run it in wine.

The software and cable are the same for Sauter TC, TE, TF, TG, SU, HD, TD.


## Protocol
The device runs at 2400baud and sends 0x10 around twice a second (which indicates that a new measurement is available). Each time you answer with 0x20, the device responds with a message containing the mode (Lp, Lq,.. fast/slow,..) and the value.

On the SU 130, the message is 0x08 0x04 MODE 0x0A 0x0A V1 V2 V3 0x01 CHECKSUM

Look into the code for further details.
