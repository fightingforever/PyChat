all:yyserver yyclient

yyserver:yyserver.c
	gcc -std=c11 -Wall -o yyserver yyserver.c `pkg-config --cflags --libs libpulse-simple`

yyclient:yyclient.c
	gcc -std=c11 -Wall -o yyclient yyclient.c `pkg-config --cflags --libs libpulse-simple`
