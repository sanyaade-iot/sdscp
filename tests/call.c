main() {
	headed(12, 5+79, ram[12+5]+sys[99+ram[12*sys[999+54]]]);

	recurs(5);

	moo: goto moo;
}

headed(a, b, c) {
	echo("a + b =", a + b, ", c = ", c);
}

recurs(a) {
	echo(a);
	if(a==0) goto end;

	recurs(a-1);

	end:
}
