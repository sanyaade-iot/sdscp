#pragma renderer sds2

#pragma check_stack_bounds false
#pragma header "moo.txt"

main()
{
	for(var i=0; i<100; i++) {
		echo(i*2);
	}

	for(var i=0; i<100; i++) {
		echo(i*3);
	}
}
